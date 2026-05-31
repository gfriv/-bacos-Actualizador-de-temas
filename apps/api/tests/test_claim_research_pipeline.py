from app.db.models import DocumentSection, Project
from app.research.schemas import SearchResult
from app.services.claim_extractor import ClaimType, extract_claims, profile_sections
from app.services.evidence import build_evidence_sources
from app.services.normative_engine import build_normative_context
from app.services.research_planner import build_research_plan
from app.services.resources import build_document_blueprint
from app.services.source_ranker import rank_sources_for_claims


def make_project() -> Project:
    return Project(
        id=1,
        owner_id=1,
        title="Tema de oposicion de Primaria",
        area="Educacion Primaria",
        educational_level="Oposiciones Educacion Primaria",
        legal_framework="Extremadura LOMLOE Decreto 107/2022 convocatoria",
        bibliography_notes="Manual base indicado por el profesor.",
    )


def make_sections() -> list[DocumentSection]:
    return [
        DocumentSection(
            id=1,
            project_id=1,
            title="Marco normativo",
            order_index=0,
            content=(
                "Actualmente la LOMCE organiza las competencias y criterios de evaluacion. "
                "La normativa de Extremadura debe relacionarse con saberes basicos."
            ),
            detected_concepts=["competencias", "criterios"],
        ),
        DocumentSection(
            id=2,
            project_id=1,
            title="Fundamentacion cientifica",
            order_index=1,
            content=(
                "Estudios recientes de 2014 indican que la recuperacion espaciada mejora el aprendizaje. "
                "Segun investigaciones recientes, este modelo debe aplicarse en el aula."
            ),
            detected_concepts=["recuperacion espaciada", "aprendizaje"],
        ),
    ]


def test_extract_claims_classifies_legal_scientific_and_dated_claims() -> None:
    claims = extract_claims(make_project(), make_sections())

    assert any(claim.claim_type == ClaimType.legal for claim in claims)
    assert any(claim.claim_type == ClaimType.scientific for claim in claims)
    assert any(claim.claim_type == ClaimType.bibliographic for claim in claims)
    assert any("LOMCE" in claim.text for claim in claims)
    assert all(claim.review_priority in {"high", "medium", "low"} for claim in claims)


def test_research_plan_prioritizes_official_and_academic_queries() -> None:
    claims = extract_claims(make_project(), make_sections())
    plan = build_research_plan(make_project(), make_sections(), claims)

    assert plan.claims == tuple(claims)
    assert any(query.layer == "official_normative" and "site:boe.es" in query.query for query in plan.queries)
    assert any(query.layer == "regional_normative" and "Extremadura" in query.query for query in plan.queries)
    assert any(query.layer == "academic" for query in plan.queries)
    assert plan.max_queries <= 12


def test_source_ranker_prefers_official_sources_for_legal_claims() -> None:
    claims = extract_claims(make_project(), make_sections())
    legal_claim = next(claim for claim in claims if claim.claim_type == ClaimType.legal)
    results = [
        SearchResult(
            title="Blog sobre competencias",
            url="https://example.com/blog-competencias",
            snippet="Resumen general sin fuente oficial.",
            source="fake",
        ),
        SearchResult(
            title="Decreto 107/2022 curriculo Primaria Extremadura",
            url="https://doe.juntaex.es/eli/es-ex/d/2022/07/28/107/con/20230919/spa/pdf",
            snippet="Curriculo de Educacion Primaria para Extremadura.",
            source="DOE directo",
        ),
    ]

    ranked = rank_sources_for_claims(results, [legal_claim], make_project())

    assert str(ranked[0].result.url).startswith("https://doe.juntaex.es")
    assert ranked[0].source_kind == "official"
    assert ranked[0].legal_relevance_score > ranked[1].legal_relevance_score

    stored = build_evidence_sources(
        project_id=1,
        analysis_run_id=1,
        results=[item.result for item in ranked],
        rankings=ranked,
    )
    assert stored[0].quality_score == ranked[0].total_score
    assert "autoridad" in (stored[0].rationale or "")


def test_normative_context_builds_stage_and_region_hierarchy() -> None:
    context = build_normative_context(make_project())

    assert context.requires_official_validation is True
    assert any(item.level == "state_curriculum" for item in context.items)
    assert any(item.level == "regional_curriculum" for item in context.items)
    assert any(item.level == "opposition_call" for item in context.items)


def test_document_blueprint_extracts_sections_and_key_concepts() -> None:
    blueprint = build_document_blueprint("# Tema\n\n## Marco normativo\n\nCompetencias y criterios.\n\n## Desarrollo\n\nAprendizaje.")

    assert blueprint.title == "Tema"
    assert [section.title for section in blueprint.sections] == ["Marco normativo", "Desarrollo"]
    assert "competencias" in blueprint.key_terms


def test_profile_sections_labels_normative_and_scientific_sections() -> None:
    profiles = profile_sections(make_sections())

    assert profiles[0].section_type == "normative"
    assert profiles[1].section_type == "scientific"
