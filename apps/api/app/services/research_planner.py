from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.db.models import DocumentSection, Project
from app.services.claim_extractor import ClaimType, DocumentClaim
from app.services.normative_engine import NormativeContext, build_normative_context


@dataclass(frozen=True)
class PlannedQuery:
    query: str
    layer: str
    priority: int
    claim_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResearchPlan:
    claims: tuple[DocumentClaim, ...]
    queries: tuple[PlannedQuery, ...]
    normative_context: NormativeContext
    max_queries: int = 12


def build_research_plan(
    project: Project,
    sections: list[DocumentSection],
    claims: list[DocumentClaim],
    max_queries: int = 12,
) -> ResearchPlan:
    normative_context = build_normative_context(project)
    queries: list[PlannedQuery] = []
    queries.extend(_official_queries(project, claims))
    queries.extend(_regional_queries(project, claims))
    queries.extend(_academic_queries(project, claims))
    queries.extend(_bibliographic_queries(project, sections, claims))
    unique = _dedupe_queries(queries)
    return ResearchPlan(
        claims=tuple(claims),
        queries=tuple(sorted(unique, key=lambda item: item.priority)[:max_queries]),
        normative_context=normative_context,
        max_queries=max_queries,
    )


def queries_from_plan(plan: ResearchPlan) -> list[str]:
    return [query.query for query in plan.queries]


def format_research_plan_markdown(plan: ResearchPlan) -> str:
    if not plan.queries:
        return "- No se han planificado busquedas."
    return "\n".join(
        f"- **{query.layer}** · prioridad {query.priority}: `{query.query}`" for query in plan.queries
    )


def _official_queries(project: Project, claims: list[DocumentClaim]) -> list[PlannedQuery]:
    current_year = datetime.now(UTC).year
    base = _base_context(project)
    legal_claim_ids = tuple(claim.id for claim in claims if claim.claim_type in {ClaimType.legal, ClaimType.curricular})
    return [
        PlannedQuery(
            query=f"{base} curriculo competencias criterios saberes basicos vigente {current_year} site:boe.es",
            layer="official_normative",
            priority=1,
            claim_ids=legal_claim_ids,
        ),
        PlannedQuery(
            query=f"{base} LOMLOE real decreto ensenanzas minimas site:boe.es",
            layer="official_normative",
            priority=2,
            claim_ids=legal_claim_ids,
        ),
    ]


def _regional_queries(project: Project, claims: list[DocumentClaim]) -> list[PlannedQuery]:
    context = _base_context(project)
    text = _normalize(f"{project.area} {project.educational_level} {project.legal_framework}")
    if "extremadura" not in text and "juntaex" not in text and "educarex" not in text:
        return []
    claim_ids = tuple(claim.id for claim in claims if claim.claim_type in {ClaimType.legal, ClaimType.curricular})
    return [
        PlannedQuery(
            query=f"{context} Extremadura DOE curriculo LOMLOE competencias criterios saberes basicos site:doe.juntaex.es",
            layer="regional_normative",
            priority=1,
            claim_ids=claim_ids,
        ),
        PlannedQuery(
            query=f"{context} Extremadura Educarex normativa evaluacion convocatoria site:educarex.es",
            layer="regional_normative",
            priority=3,
            claim_ids=claim_ids,
        ),
    ]


def _academic_queries(project: Project, claims: list[DocumentClaim]) -> list[PlannedQuery]:
    scientific_claims = [claim for claim in claims if claim.claim_type in {ClaimType.scientific, ClaimType.bibliographic}]
    if not scientific_claims:
        return []
    current_year = datetime.now(UTC).year
    queries = []
    for claim in scientific_claims[:4]:
        terms = " ".join(claim.search_terms[:8])
        queries.append(
            PlannedQuery(
                query=f"{terms} revision evidencia educativa {current_year - 3} {current_year} doi OR revista",
                layer="academic",
                priority=4 if claim.review_priority == "high" else 5,
                claim_ids=(claim.id,),
            )
        )
    return queries


def _bibliographic_queries(
    project: Project,
    sections: list[DocumentSection],
    claims: list[DocumentClaim],
) -> list[PlannedQuery]:
    terms = " ".join([project.area, project.educational_level, *[section.title for section in sections[:3]]])
    claim_ids = tuple(claim.id for claim in claims if claim.claim_type == ClaimType.bibliographic)
    return [
        PlannedQuery(
            query=f"{terms} bibliografia actualizada manual referencia didactica",
            layer="bibliographic",
            priority=7,
            claim_ids=claim_ids,
        )
    ]


def _dedupe_queries(queries: list[PlannedQuery]) -> list[PlannedQuery]:
    seen: set[str] = set()
    deduped: list[PlannedQuery] = []
    for query in queries:
        key = _normalize(query.query)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(query)
    return deduped


def _base_context(project: Project) -> str:
    return " ".join(
        item
        for item in [project.area, project.educational_level, project.legal_framework]
        if item and item.strip()
    )


def _normalize(text: str) -> str:
    replacements = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return " ".join(text.translate(replacements).lower().split())
