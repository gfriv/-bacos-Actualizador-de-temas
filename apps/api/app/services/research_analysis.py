from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from unicodedata import normalize

import httpx
from bs4 import BeautifulSoup

from app.core.brand import (
    build_ai_notice,
    build_artifact_header,
    build_corporate_footer,
    generated_at_iso,
)
from app.core.config import settings
from app.db.models import (
    DocumentSection,
    Project,
    Report,
    ReportType,
    Suggestion,
    SuggestionStatus,
    SuggestionType,
)
from app.llm.model_router import ModelRouter
from app.llm.schemas import (
    AIProviderConfig,
    ModelConfig,
)
from app.llm.schemas import (
    CurriculumSuggestion as CurriculumSuggestionSchema,
)
from app.llm.schemas import (
    ScientificSuggestion as ScientificSuggestionSchema,
)
from app.research.schemas import SearchResult
from app.research.source_policy import (
    format_assessments_markdown,
    is_official_url,
    validation_summary,
)
from app.research.web_search import WebSearchProvider, get_web_search_provider
from app.services.academic_rubric import (
    AcademicRubricResult,
    evaluate_academic_rubric,
    format_academic_rubric_markdown,
    select_section_for_code,
)
from app.services.claim_extractor import (
    ClaimType,
    DocumentClaim,
    extract_claims,
    format_claims_markdown,
    profile_sections,
)
from app.services.normative_engine import format_normative_context_markdown
from app.services.research_planner import (
    ResearchPlan,
    build_research_plan,
    format_research_plan_markdown,
    queries_from_plan,
)
from app.services.source_ranker import (
    RankedSource,
    format_ranked_sources_markdown,
    rank_sources_for_claims,
)

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"
CURATED_CURRICULUM_SOURCES = {
    "infantil": [
        (
            "Real Decreto 95/2022, de enseñanzas mínimas de Educación Infantil",
            "https://www.boe.es/buscar/act.php?id=BOE-A-2022-1654",
        )
    ],
    "primaria": [
        (
            "Real Decreto 157/2022, de enseñanzas mínimas de Educación Primaria",
            "https://www.boe.es/buscar/act.php?id=BOE-A-2022-3296",
        )
    ],
    "eso": [
        (
            "Real Decreto 217/2022, de enseñanzas mínimas de Educación Secundaria Obligatoria",
            "https://www.boe.es/buscar/act.php?id=BOE-A-2022-4975",
        )
    ],
    "bachillerato": [
        (
            "Real Decreto 243/2022, de enseñanzas mínimas de Bachillerato",
            "https://www.boe.es/buscar/act.php?id=BOE-A-2022-5521",
        )
    ],
    "fp": [
        (
            "Ley Orgánica 3/2022, de ordenación e integración de la Formación Profesional",
            "https://www.boe.es/buscar/act.php?id=BOE-A-2022-5139",
        ),
        (
            "Real Decreto 659/2023, de ordenación del Sistema de Formación Profesional",
            "https://www.boe.es/buscar/act.php?id=BOE-A-2023-16889",
        ),
    ],
}
LOMLOE_SOURCE = (
    "Ley Orgánica 3/2020, de modificación de la Ley Orgánica de Educación",
    "https://www.boe.es/buscar/act.php?id=BOE-A-2020-17264",
)
OPPOSITION_SOURCE = (
    "Real Decreto 276/2007, de ingreso, accesos y nuevas especialidades en cuerpos docentes",
    "https://www.boe.es/buscar/act.php?id=BOE-A-2007-4372",
)
EXTREMADURA_GENERAL_SOURCES = [
    (
        "Ley 4/2011, de Educación de Extremadura",
        "https://www.boe.es/eli/es-ex/l/2011/03/07/4/con",
    ),
    (
        "Orden de 9 de diciembre de 2022, evaluación en Infantil, Primaria, ESO y Bachillerato en Extremadura",
        "https://doe.juntaex.es/eli/es-ex/o/2022/12/09/(1)/con/20250930/spa/pdf",
    ),
]
EXTREMADURA_CURRICULUM_SOURCES = {
    "infantil": [
        (
            "Decreto 98/2022, currículo de Educación Infantil para Extremadura",
            "https://doe.juntaex.es/eli/es-ex/d/2022/07/20/98/con/20230919/spa/pdf",
        )
    ],
    "primaria": [
        (
            "Decreto 107/2022, currículo de Educación Primaria para Extremadura",
            "https://doe.juntaex.es/eli/es-ex/d/2022/07/28/107/con/20230919/spa/pdf",
        )
    ],
    "eso": [
        (
            "Decreto 110/2022, currículo de Educación Secundaria Obligatoria para Extremadura",
            "https://doe.juntaex.es/eli/es-ex/d/2022/08/22/110/con/20230919/spa/pdf",
        )
    ],
    "bachillerato": [
        (
            "Decreto 109/2022, currículo de Bachillerato para Extremadura",
            "https://doe.juntaex.es/eli/es-ex/d/2022/08/22/109/con/20230919/spa/pdf",
        )
    ],
    "fp": [
        (
            "Decreto 14/2022, evaluación, promoción y titulación en Extremadura, incluida Formación Profesional",
            "https://doe.juntaex.es/eli/es-ex/d/2022/02/18/14/con/20220825/spa/pdf",
        )
    ],
}


@dataclass
class ResearchAnalysisResult:
    reports: list[Report]
    suggestions: list[Suggestion]
    queries: list[str]
    evidence: list[SearchResult]
    claims: list[DocumentClaim] | None = None
    ranked_sources: list[RankedSource] | None = None
    llm_used: bool = False
    llm_degraded: bool = False
    web_search_used: bool = False
    official_sources_used: bool = False
    academic_score: int | None = None
    warnings: list[str] | None = None


async def build_research_analysis(
    project: Project,
    sections: list[DocumentSection],
    search_provider: WebSearchProvider | None = None,
    provider_config: AIProviderConfig | None = None,
) -> ResearchAnalysisResult:
    provider = search_provider or get_web_search_provider(
        provider_config.web_search_provider if provider_config else None,
        enabled=provider_config.web_search_enabled if provider_config else None,
    )
    generated_at = generated_at_iso()
    provider_name, model_name = describe_ai_provider(provider_config)
    claims = extract_claims(project, sections)
    plan = build_research_plan(project, sections, claims)
    queries = queries_from_plan(plan) or build_search_queries(project, sections)
    curated_evidence = await collect_curated_curriculum_evidence(project) if should_fetch_official_sources(search_provider) else []
    queries_to_run = queries[:2] if curated_evidence else queries
    evidence = await collect_evidence(provider, queries_to_run)
    evidence = merge_evidence([result for result in evidence if is_available_evidence(result)], curated_evidence)
    official_evidence = [result for result in evidence if is_official_source(str(result.url))]
    if not official_evidence and allows_external_research(provider):
        curated_evidence = await collect_curated_curriculum_evidence(project)
        if curated_evidence:
            evidence = merge_evidence([result for result in evidence if is_available_evidence(result)], curated_evidence)
        official_evidence = [result for result in evidence if is_official_source(str(result.url))]
    scientific_evidence = [
        result for result in evidence if is_available_evidence(result) and not is_official_source(str(result.url))
    ]
    ranked_sources = rank_sources_for_claims(evidence, claims, project)
    if ranked_sources:
        evidence = [source.result for source in ranked_sources]
        official_evidence = [result for result in evidence if is_official_source(str(result.url))]
        scientific_evidence = [
            result for result in evidence if is_available_evidence(result) and not is_official_source(str(result.url))
        ]
    rubric = evaluate_academic_rubric(project, sections, evidence)

    suggestions, llm_used, llm_degraded = await build_suggestions(
        project,
        sections,
        scientific_evidence,
        official_evidence,
        evidence,
        rubric,
        claims,
        ranked_sources,
        provider_config,
    )
    warnings: list[str] = []
    if llm_degraded:
        warnings.append("El LLM no ha devuelto una salida estructurada valida; se ha generado analisis degradado.")
    if not evidence:
        warnings.append("No se han recuperado evidencias externas; todas las propuestas requieren verificacion docente.")
    for finding in rubric.findings:
        if finding.severity == "high":
            warnings.append(f"Riesgo alto en {finding.section_title}: {finding.message}")
    reports = build_structured_reports(
        project=project,
        sections=sections,
        evidence=evidence,
        scientific_evidence=scientific_evidence,
        official_evidence=official_evidence,
        queries=queries,
        suggestions=suggestions,
        generated_at=generated_at,
        provider_name=provider_name,
        model_name=model_name,
        llm_degraded=llm_degraded,
        warnings=warnings,
        rubric=rubric,
        claims=claims,
        plan=plan,
        ranked_sources=ranked_sources,
    )
    return ResearchAnalysisResult(
        reports=reports,
        suggestions=suggestions,
        queries=queries,
        evidence=evidence,
        llm_used=llm_used,
        llm_degraded=llm_degraded,
        web_search_used=allows_external_research(provider),
        official_sources_used=bool(curated_evidence),
        academic_score=rubric.score,
        claims=claims,
        ranked_sources=ranked_sources,
        warnings=warnings,
    )


def build_search_queries(project: Project, sections: list[DocumentSection]) -> list[str]:
    concepts = extract_concept_terms(sections)
    concept_query = " ".join(concepts[:6])
    area_level = f"{project.area} {project.educational_level}".strip()
    legal = project.legal_framework.strip()
    current_year = datetime.now(UTC).year
    expanded_level = expand_educational_level(project.educational_level)

    queries = [
        f"{area_level} {concept_query} actualización científica revisión {current_year - 1} {current_year}",
        f"{area_level} {concept_query} evidencia científica reciente educación",
    ]
    if legal:
        queries.extend(
            [
                f"{legal} {area_level} currículo competencias criterios saberes básicos vigente {current_year} site:boe.es",
                f"{legal} {area_level} normativa currículo vigente {current_year} site:educagob.educacionfpydeportes.gob.es",
                f"{legal} {area_level} currículo educación vigente {current_year} site:educacionfpydeportes.gob.es",
                f"{legal} {expanded_level} currículo básico competencias criterios saberes básicos site:boe.es",
                f"LOMLOE {expanded_level or project.educational_level} currículo competencias criterios saberes básicos site:boe.es",
            ]
        )
        if is_extremadura_context(f"{legal} {area_level}"):
            queries.extend(
                [
                    f"{legal} {area_level} Extremadura currículo DOE competencias criterios saberes básicos site:doe.juntaex.es",
                    f"{legal} {expanded_level} Extremadura LOMLOE currículo evaluación site:doe.juntaex.es",
                    f"{legal} {area_level} Extremadura Educarex currículo LOMLOE site:educarex.es",
                ]
            )
    return unique_query_variants(queries)


async def collect_evidence(provider: WebSearchProvider, queries: list[str]) -> list[SearchResult]:
    semaphore = asyncio.Semaphore(4)

    async def run_query(query: str) -> list[SearchResult]:
        async with semaphore:
            try:
                return await provider.search(query)
            except Exception as exc:
                return [
                    SearchResult(
                        title="Búsqueda no disponible",
                        url="https://example.invalid/search-unavailable",
                        snippet=f"No se pudo consultar {provider.name}: {exc}",
                        source=provider.name,
                    )
                ]

    seen: set[str] = set()
    evidence: list[SearchResult] = []
    query_results = await asyncio.gather(*(run_query(query) for query in queries))
    for results in query_results:
        for result in results:
            url = str(result.url)
            if url in seen:
                continue
            seen.add(url)
            evidence.append(result)
    return evidence


def allows_external_research(provider: WebSearchProvider) -> bool:
    return provider.name not in {"disabled", "none", "off"}


def should_fetch_official_sources(search_provider: WebSearchProvider | None) -> bool:
    return search_provider is None and settings.official_source_fetch_enabled


async def collect_curated_curriculum_evidence(project: Project) -> list[SearchResult]:
    sources = official_curriculum_sources(project)
    if not sources:
        return []

    results: list[SearchResult] = []
    async with httpx.AsyncClient(timeout=settings.web_search_timeout_seconds) as client:
        for title, url in sources:
            snippet = "Fuente oficial para contraste curricular. Requiere lectura y validación docente."
            source_name = "DOE directo" if "doe.juntaex.es" in url else "BOE directo"
            try:
                response = await client.get(url)
                response.raise_for_status()
                snippet = extract_curriculum_snippet(response.text) or snippet
            except Exception:
                pass
            results.append(SearchResult(title=title, url=url, snippet=snippet, source=source_name))
    return results


def official_curriculum_sources(project: Project) -> list[tuple[str, str]]:
    level_key = normalize_query_text(f"{project.educational_level} {project.legal_framework}").lower()
    sources: list[tuple[str, str]] = []
    if "lomloe" in level_key:
        sources.append(LOMLOE_SOURCE)
    if "oposicion" in level_key or "oposiciones" in level_key or "concurso-oposicion" in level_key:
        sources.append(OPPOSITION_SOURCE)
    if is_extremadura_context(level_key):
        sources.extend(EXTREMADURA_GENERAL_SOURCES)
    if "infantil" in level_key:
        sources.extend(CURATED_CURRICULUM_SOURCES["infantil"])
        if is_extremadura_context(level_key):
            sources.extend(EXTREMADURA_CURRICULUM_SOURCES["infantil"])
    if "primaria" in level_key:
        sources.extend(CURATED_CURRICULUM_SOURCES["primaria"])
        if is_extremadura_context(level_key):
            sources.extend(EXTREMADURA_CURRICULUM_SOURCES["primaria"])
    if "eso" in level_key or "secundaria" in level_key:
        sources.extend(CURATED_CURRICULUM_SOURCES["eso"])
        if is_extremadura_context(level_key):
            sources.extend(EXTREMADURA_CURRICULUM_SOURCES["eso"])
    if "bachiller" in level_key:
        sources.extend(CURATED_CURRICULUM_SOURCES["bachillerato"])
        if is_extremadura_context(level_key):
            sources.extend(EXTREMADURA_CURRICULUM_SOURCES["bachillerato"])
    if "fp" in level_key or "formacion profesional" in level_key:
        sources.extend(CURATED_CURRICULUM_SOURCES["fp"])
        if is_extremadura_context(level_key):
            sources.extend(EXTREMADURA_CURRICULUM_SOURCES["fp"])
    return list(dict.fromkeys(sources))


def extract_curriculum_snippet(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.get_text(" ", strip=True).split())
    lowered = text.lower()
    anchors = ["currículo", "competencias", "criterios de evaluación", "saberes básicos"]
    positions = [lowered.find(anchor) for anchor in anchors if lowered.find(anchor) != -1]
    if not positions:
        return text[:700] if text else None
    start = max(min(positions) - 180, 0)
    return text[start : start + 900]


def merge_evidence(primary: list[SearchResult], secondary: list[SearchResult]) -> list[SearchResult]:
    seen = {str(result.url) for result in primary}
    merged = list(primary)
    for result in secondary:
        if str(result.url) in seen:
            continue
        seen.add(str(result.url))
        merged.append(result)
    return merged


def describe_ai_provider(provider_config: AIProviderConfig | None) -> tuple[str, str | None]:
    if provider_config is not None:
        return provider_config.provider_id, provider_config.model
    return settings.llm_provider, settings.llm_model or ("MockProvider" if settings.llm_provider == "mock" else None)


def build_structured_reports(
    *,
    project: Project,
    sections: list[DocumentSection],
    evidence: list[SearchResult],
    scientific_evidence: list[SearchResult],
    official_evidence: list[SearchResult],
    queries: list[str],
    suggestions: list[Suggestion],
    generated_at: str,
    provider_name: str,
    model_name: str | None,
    llm_degraded: bool,
    warnings: list[str],
    rubric: AcademicRubricResult,
    claims: list[DocumentClaim],
    plan: ResearchPlan,
    ranked_sources: list[RankedSource],
) -> list[Report]:
    return [
        Report(
            project_id=project.id,
            report_type=ReportType.initial_diagnosis,
            title="Diagnóstico inicial del tema",
            content_markdown=compose_report(
                title="Diagnóstico inicial del tema",
                project=project,
                generated_at=generated_at,
                provider_name=provider_name,
                model_name=model_name,
                body=build_initial_diagnosis_report(project, sections, evidence, warnings, rubric, claims, plan),
            ),
        ),
        Report(
            project_id=project.id,
            report_type=ReportType.scientific_update,
            title="Informe de actualización científica con búsqueda web",
            content_markdown=compose_report(
                title="Informe de actualización científica",
                project=project,
                generated_at=generated_at,
                provider_name=provider_name,
                model_name=model_name,
                body=build_scientific_report(project, sections, evidence, queries, rubric, claims, ranked_sources),
            ),
        ),
        Report(
            project_id=project.id,
            report_type=ReportType.curriculum_mapping,
            title="Informe legislativo y curricular con fuentes trazables",
            content_markdown=compose_report(
                title="Informe legislativo y curricular",
                project=project,
                generated_at=generated_at,
                provider_name=provider_name,
                model_name=model_name,
                body=build_curriculum_report(project, official_evidence, evidence, queries, rubric, claims, plan),
            ),
        ),
        Report(
            project_id=project.id,
            report_type=ReportType.source_validation,
            title="Informe de validación de fuentes",
            content_markdown=compose_report(
                title="Informe de validación de fuentes",
                project=project,
                generated_at=generated_at,
                provider_name=provider_name,
                model_name=model_name,
                body=build_source_validation_report(scientific_evidence, official_evidence, evidence, rubric, ranked_sources),
            ),
        ),
        Report(
            project_id=project.id,
            report_type=ReportType.change_proposal,
            title="Informe de propuestas de cambio",
            content_markdown=compose_report(
                title="Informe de propuestas de cambio",
                project=project,
                generated_at=generated_at,
                provider_name=provider_name,
                model_name=model_name,
                body=build_change_proposal_report(suggestions),
            ),
        ),
        Report(
            project_id=project.id,
            report_type=ReportType.technical_traceability,
            title="Informe técnico de trazabilidad",
            content_markdown=compose_report(
                title="Informe técnico de trazabilidad",
                project=project,
                generated_at=generated_at,
                provider_name=provider_name,
                model_name=model_name,
                body=build_traceability_report(sections, evidence, queries, suggestions, llm_degraded, rubric, claims, plan),
            ),
        ),
    ]


def compose_report(
    *,
    title: str,
    project: Project,
    generated_at: str,
    provider_name: str,
    model_name: str | None,
    body: str,
) -> str:
    return "\n\n".join(
        [
            build_artifact_header(
                title=title,
                project_title=project.title,
                generated_at=generated_at,
                provider=provider_name,
                model=model_name,
            ),
            body,
            build_ai_notice(),
            build_corporate_footer(),
        ]
    )


def build_initial_diagnosis_report(
    project: Project,
    sections: list[DocumentSection],
    evidence: list[SearchResult],
    warnings: list[str],
    rubric: AcademicRubricResult,
    claims: list[DocumentClaim],
    plan: ResearchPlan,
) -> str:
    concepts = ", ".join(extract_concept_terms(sections)[:12]) or "conceptos pendientes de detección"
    characters = sum(len(section.content) for section in sections)
    warnings_block = "\n".join(f"- {warning}" for warning in warnings) or "- Sin advertencias operativas."
    profiles_block = "\n".join(
        f"- **{profile.title}**: {profile.section_type}; riesgos {', '.join(profile.risk_flags) or 'sin riesgos automaticos'}."
        for profile in profile_sections(sections)
    )
    return (
        "## Alcance del análisis\n\n"
        f"- Área/especialidad: **{project.area}**.\n"
        f"- Nivel educativo: **{project.educational_level}**.\n"
        f"- Normativa aportada: **{project.legal_framework}**.\n"
        f"- Secciones detectadas: **{len(sections)}**.\n"
        f"- Extensión textual aproximada: **{characters} caracteres**.\n"
        f"- Conceptos priorizados: {concepts}.\n\n"
        "## Diagnóstico operativo\n\n"
        "- El tema tiene estructura suficiente para revisión por secciones.\n"
        "- Las sugerencias deben mantenerse localizadas y trazables.\n"
        f"- {validation_summary(evidence)}\n\n"
        "## Riesgos de revisión\n\n"
        "- La normativa autonómica debe confirmarse con la documentación aportada por el profesor.\n"
        "- Las referencias científicas no deben usarse si no pueden verificarse de forma independiente.\n"
        "- La consolidación queda bloqueada si no hay sugerencias aprobadas o editadas.\n\n"
        "## Advertencias operativas\n\n"
        f"{warnings_block}\n\n"
        "## Claims detectados\n\n"
        f"{format_claims_markdown(claims)}\n\n"
        "## Perfil de secciones\n\n"
        f"{profiles_block}\n\n"
        "## Plan de investigacion\n\n"
        f"{format_research_plan_markdown(plan)}\n\n"
        f"{format_academic_rubric_markdown(rubric)}"
    )


def build_scientific_report(
    project: Project,
    sections: list[DocumentSection],
    evidence: list[SearchResult],
    queries: list[str],
    rubric: AcademicRubricResult,
    claims: list[DocumentClaim],
    ranked_sources: list[RankedSource],
) -> str:
    concepts = ", ".join(extract_concept_terms(sections)[:10]) or "conceptos del documento"
    evidence_markdown = format_evidence(evidence[:8])
    return (
        "## Diagnóstico inicial\n\n"
        f"- Área/nivel: **{project.area} · {project.educational_level}**.\n"
        f"- Conceptos detectados para contraste: {concepts}.\n"
        "- Las propuestas se mantienen localizadas y requieren validación docente.\n\n"
        "## Búsquedas realizadas\n\n"
        f"{format_queries(queries[:2])}\n\n"
        "## Fuentes encontradas\n\n"
        f"{evidence_markdown}\n\n"
        "## Afirmaciones cientificas o bibliograficas a verificar\n\n"
        f"{format_claims_markdown([claim for claim in claims if claim.claim_type in {ClaimType.scientific, ClaimType.bibliographic}])}\n\n"
        "## Ranking de fuentes para actualizacion\n\n"
        f"{format_ranked_sources_markdown(ranked_sources)}\n\n"
        "## Calidad de fuentes\n\n"
        f"{format_assessments_markdown(evidence[:8])}\n\n"
        "## Riesgos académicos relevantes\n\n"
        f"{format_rubric_findings_for_report(rubric, {'scientific_claim_without_academic_evidence', 'dated_claim_with_current_language', 'possible_outdated_law_reference'})}\n\n"
        "## Criterio de uso\n\n"
        "- No se inventan referencias.\n"
        "- Si una fuente no es suficientemente específica, la sugerencia queda como aspecto a verificar.\n"
        "- El profesor debe revisar fuente, pertinencia y redacción antes de consolidar."
    )


def build_curriculum_report(
    project: Project,
    official_evidence: list[SearchResult],
    all_evidence: list[SearchResult],
    queries: list[str],
    rubric: AcademicRubricResult,
    claims: list[DocumentClaim],
    plan: ResearchPlan,
) -> str:
    official_markdown = format_evidence(official_evidence[:8])
    fallback_markdown = format_evidence(all_evidence[:5])
    sources_block = official_markdown if official_evidence else fallback_markdown
    confidence = (
        "Hay fuentes oficiales localizadas para contraste."
        if official_evidence
        else "No se han localizado suficientes fuentes oficiales; requiere verificación manual."
    )
    return (
        "## Contextualización legislativa y curricular\n\n"
        f"- Normativa indicada por el profesor: **{project.legal_framework}**.\n"
        f"- Resultado de trazabilidad: {confidence}\n"
        "- No se asignan competencias, criterios ni saberes si no hay base documental clara.\n\n"
        "## Búsquedas curriculares realizadas\n\n"
        f"{format_queries(queries[2:] or queries)}\n\n"
        "## Fuentes normativas o de contraste\n\n"
        f"{sources_block}\n\n"
        "## Jerarquia normativa esperada\n\n"
        f"{format_normative_context_markdown(plan.normative_context)}\n\n"
        "## Claims normativos/curriculares detectados\n\n"
        f"{format_claims_markdown([claim for claim in claims if claim.claim_type in {ClaimType.legal, ClaimType.curricular}])}\n\n"
        "## Calidad de fuentes\n\n"
        f"{format_assessments_markdown((official_evidence or all_evidence)[:8])}\n\n"
        "## Riesgos curriculares detectados\n\n"
        f"{format_rubric_findings_for_report(rubric, {'no_official_curriculum_evidence', 'possible_outdated_law_reference', 'opposition_framework_incomplete'})}\n\n"
        "## Criterio de uso docente\n\n"
        "- Validar que la normativa encontrada corresponde a la etapa, comunidad autónoma y fecha aplicable.\n"
        "- Si el centro aporta decreto autonómico o convocatoria concreta, debe prevalecer sobre resultados genéricos.\n"
        "- Las sugerencias curriculares quedan pendientes hasta revisión del profesor."
    )


def build_source_validation_report(
    scientific_evidence: list[SearchResult],
    official_evidence: list[SearchResult],
    all_evidence: list[SearchResult],
    rubric: AcademicRubricResult,
    ranked_sources: list[RankedSource],
) -> str:
    return (
        "## Resumen de validación\n\n"
        f"- {validation_summary(all_evidence)}\n"
        f"- Fuentes oficiales detectadas: **{len(official_evidence)}**.\n"
        f"- Fuentes científicas/no normativas detectadas: **{len(scientific_evidence)}**.\n\n"
        "## Evaluación fuente a fuente\n\n"
        f"{format_assessments_markdown(all_evidence[:12])}\n\n"
        "## Ranking ponderado de fuentes\n\n"
        f"{format_ranked_sources_markdown(ranked_sources)}\n\n"
        "## Rubrica academica y riesgos\n\n"
        f"{format_rubric_findings_for_report(rubric, {'missing_bibliography', 'scientific_claim_without_academic_evidence', 'no_official_curriculum_evidence'})}\n\n"
        "## Decisión de uso\n\n"
        "- Confirmado: puede fundamentar una sugerencia, siempre con lectura docente.\n"
        "- Probable: requiere comprobar pertinencia, fecha y fragmento exacto.\n"
        "- Requiere verificación: no debe incorporarse sin revisión manual explícita."
    )


def build_change_proposal_report(suggestions: list[Suggestion]) -> str:
    if not suggestions:
        suggestions_block = "- No se han generado sugerencias."
    else:
        suggestions_block = "\n".join(
            (
                f"- **{suggestion.suggestion_type.value}** · confianza {suggestion.confidence_level}: "
                f"{fragment(suggestion.proposed_change, 220)} "
                f"Referencia: {suggestion.source_reference or 'requiere verificación'}."
            )
            for suggestion in suggestions
        )
    return (
        "## Propuestas revisables\n\n"
        f"{suggestions_block}\n\n"
        "## Regla de integración\n\n"
        "- Estado `pending`: no se integra.\n"
        "- Estado `rejected`: no se integra.\n"
        "- Estado `approved`: se integra si el fragmento original encaja.\n"
        "- Estado `edited`: se integra usando la versión editada por el docente."
    )


def build_traceability_report(
    sections: list[DocumentSection],
    evidence: list[SearchResult],
    queries: list[str],
    suggestions: list[Suggestion],
    llm_degraded: bool,
    rubric: AcademicRubricResult,
    claims: list[DocumentClaim],
    plan: ResearchPlan,
) -> str:
    return (
        "## Trazabilidad técnica\n\n"
        f"- Secciones procesadas: **{len(sections)}**.\n"
        f"- Consultas preparadas: **{len(queries)}**.\n"
        f"- Claims detectados: **{len(claims)}**.\n"
        f"- Evidencias recuperadas: **{len(evidence)}**.\n"
        f"- Sugerencias generadas: **{len(suggestions)}**.\n\n"
        "## Estado LLM\n\n"
        f"- Sintesis LLM degradada: **{'si' if llm_degraded else 'no'}**.\n\n"
        "## Rúbrica académica\n\n"
        f"- Puntuación técnica: **{rubric.score}/100**.\n"
        f"- Riesgos altos: **{rubric.high_risk_count}**.\n"
        f"- Fuentes oficiales: **{rubric.official_evidence_count}**.\n"
        f"- Fuentes académicas/editoriales: **{rubric.academic_evidence_count}**.\n\n"
        "## Consultas documentadas\n\n"
        f"{format_queries(queries)}\n\n"
        "## Capas de investigacion\n\n"
        f"{format_research_plan_markdown(plan)}\n\n"
        "## Garantías aplicadas\n\n"
        "- Las claves de IA no se guardan en informes ni auditoría.\n"
        "- Las rutas internas de almacenamiento no forman parte del contenido exportable.\n"
        "- Las sugerencias conservan fragmento original, propuesta, justificación, fuente y confianza."
    )


async def build_suggestions(
    project: Project,
    sections: list[DocumentSection],
    scientific_evidence: list[SearchResult],
    official_evidence: list[SearchResult],
    all_evidence: list[SearchResult],
    rubric: AcademicRubricResult,
    claims: list[DocumentClaim],
    ranked_sources: list[RankedSource],
    provider_config: AIProviderConfig | None = None,
) -> tuple[list[Suggestion], bool, bool]:
    first = select_section_for_code(
        rubric,
        sections,
        {"scientific_claim_without_academic_evidence", "dated_claim_with_current_language"},
        fallback_index=0,
    )
    second = select_section_for_code(
        rubric,
        sections,
        {"no_official_curriculum_evidence", "possible_outdated_law_reference", "opposition_framework_incomplete"},
        fallback_index=1 if len(sections) > 1 else 0,
    )
    scientific_claim = select_claim_for_types(claims, {ClaimType.scientific, ClaimType.bibliographic})
    curriculum_claim = select_claim_for_types(claims, {ClaimType.legal, ClaimType.curricular})
    if scientific_claim:
        first = section_for_claim(sections, scientific_claim) or first
    if curriculum_claim:
        second = section_for_claim(sections, curriculum_claim) or second
    llm_suggestions, llm_degraded = await build_llm_grounded_suggestions(
        project=project,
        scientific_section=first,
        curriculum_section=second,
        scientific_evidence=scientific_evidence,
        official_evidence=official_evidence,
        all_evidence=all_evidence,
        provider_config=provider_config,
    )
    if llm_suggestions:
        suggestions = llm_suggestions
        if should_add_bibliographic_suggestion(project, all_evidence):
            suggestions.append(build_bibliographic_suggestion(project, first, all_evidence, rubric))
        return suggestions, True, False
    suggestions = [
        build_claim_scientific_suggestion(project, first, scientific_evidence, scientific_claim, ranked_sources),
        build_claim_curriculum_suggestion(project, second, official_evidence, all_evidence, curriculum_claim, ranked_sources),
    ]
    if should_add_bibliographic_suggestion(project, all_evidence):
        suggestions.append(build_bibliographic_suggestion(project, first, all_evidence, rubric))
    return suggestions, False, llm_degraded


async def build_llm_grounded_suggestions(
    project: Project,
    scientific_section: DocumentSection,
    curriculum_section: DocumentSection,
    scientific_evidence: list[SearchResult],
    official_evidence: list[SearchResult],
    all_evidence: list[SearchResult],
    provider_config: AIProviderConfig | None = None,
) -> tuple[list[Suggestion] | None, bool]:
    if provider_config is None and (not settings.analysis_llm_enabled or settings.llm_provider == "mock"):
        return None, False

    try:
        router = ModelRouter(provider_config=provider_config)
        scientific = await router.generate_json(
            prompt=build_llm_prompt(project, scientific_section, scientific_evidence[:8], "scientific"),
            system_prompt=load_system_prompt("scientific_update_system.md"),
            schema=ScientificSuggestionSchema,
            model_config=ModelConfig(temperature=0.1, max_tokens=1200),
        )
        curriculum_sources = official_evidence[:8] or all_evidence[:8]
        curriculum = await router.generate_json(
            prompt=build_llm_prompt(project, curriculum_section, curriculum_sources, "curriculum"),
            system_prompt=load_system_prompt("curriculum_mapping_system.md"),
            schema=CurriculumSuggestionSchema,
            model_config=ModelConfig(temperature=0.1, max_tokens=1200),
        )
    except Exception:
        return None, True

    scientific_fragment = scientific.original_fragment or fragment(scientific_section.content)
    curriculum_fragment = fragment(curriculum_section.content)
    return [
        Suggestion(
            project_id=project.id,
            section_id=scientific_section.id,
            suggestion_type=SuggestionType.scientific_update,
            original_fragment=scientific_fragment,
            proposed_change=scientific.proposed_change,
            justification=scientific.justification,
            source_reference=scientific.source_reference,
            confidence_level=scientific.confidence_level,
            status=SuggestionStatus.pending,
            anchor_context=build_anchor_context(scientific_section.content, scientific_fragment),
        ),
        Suggestion(
            project_id=project.id,
            section_id=curriculum_section.id,
            suggestion_type=SuggestionType.legal_curricular,
            original_fragment=curriculum_fragment,
            proposed_change=curriculum.proposed_change,
            justification=curriculum.justification,
            source_reference=curriculum.legal_reference,
            confidence_level=curriculum.confidence_level,
            status=SuggestionStatus.pending,
            anchor_context=build_anchor_context(curriculum_section.content, curriculum_fragment),
        ),
    ], False


def build_llm_prompt(
    project: Project,
    section: DocumentSection,
    evidence: list[SearchResult],
    mode: str,
) -> str:
    focus = (
        "Detecta una sugerencia de actualización científica localizada."
        if mode == "scientific"
        else "Detecta una sugerencia legislativa/curricular localizada basada solo en normativa o fuentes oficiales aportadas."
    )
    return (
        f"{focus}\n\n"
        "No inventes referencias, leyes, decretos, artículos, competencias ni criterios. "
        "Si las fuentes no permiten una propuesta concreta, marca confianza low y pide verificación docente.\n\n"
        f"Proyecto: {project.title}\n"
        f"Área o especialidad: {project.area}\n"
        f"Nivel educativo: {project.educational_level}\n"
        f"Normativa indicada por el profesor: {project.legal_framework}\n"
        f"Bibliografía base: {project.bibliography_notes or 'No indicada'}\n"
        f"Instrucciones adicionales: {project.instructions or 'No indicadas'}\n\n"
        f"Sección: {section.title}\n"
        f"Contenido de la sección:\n{fragment(section.content, 1600)}\n\n"
        "Fuentes recuperadas por búsqueda web:\n"
        f"{format_evidence_for_prompt(evidence)}"
    )


def load_system_prompt(filename: str) -> str:
    return (PROMPT_DIR / filename).read_text(encoding="utf-8")


def build_scientific_suggestion(
    project: Project,
    section: DocumentSection,
    evidence: list[SearchResult],
    claim: DocumentClaim | None = None,
    ranked_sources: list[RankedSource] | None = None,
) -> Suggestion:
    source = format_source_reference(evidence[:3]) or "Búsqueda web sin resultados suficientes; requiere verificación."
    return Suggestion(
        project_id=project.id,
        section_id=section.id,
        suggestion_type=SuggestionType.scientific_update,
        original_fragment=fragment(section.content),
        proposed_change=(
            "Revisar este fragmento frente a fuentes recientes localizadas y actualizar solo la formulación "
            "que el docente confirme como vigente."
        ),
        justification=(
            "La búsqueda externa aporta contexto actualizado, pero la app no integra cambios sin revisión humana."
        ),
        source_reference=source,
        confidence_level="medium" if evidence else "low",
        status=SuggestionStatus.pending,
        anchor_context=build_anchor_context(section.content, fragment(section.content)),
    )


def build_curriculum_suggestion(
    project: Project,
    section: DocumentSection,
    official_evidence: list[SearchResult],
    all_evidence: list[SearchResult],
) -> Suggestion:
    usable = official_evidence or all_evidence
    source = format_source_reference(usable[:3]) or project.legal_framework
    confidence = "high" if official_evidence else "low"
    return Suggestion(
        project_id=project.id,
        section_id=section.id,
        suggestion_type=SuggestionType.legal_curricular,
        original_fragment=fragment(section.content),
        proposed_change=(
            f"Añadir una conexión curricular localizada para «{section.title}» usando el marco "
            f"«{project.legal_framework}» y las fuentes oficiales recuperadas. El docente debe seleccionar "
            "las competencias, criterios o saberes exactos únicamente tras comprobar que la norma corresponde "
            "al nivel, comunidad autónoma y fecha aplicable."
        ),
        justification=(
            "La sugerencia curricular se basa en búsqueda de normativa/fuentes oficiales y queda pendiente de "
            "validación docente obligatoria."
        ),
        source_reference=source,
        confidence_level=confidence,
        status=SuggestionStatus.pending,
        anchor_context=build_anchor_context(section.content, fragment(section.content)),
    )


def should_add_bibliographic_suggestion(project: Project, evidence: list[SearchResult]) -> bool:
    return not (project.bibliography_notes or "").strip() or not evidence


def build_claim_scientific_suggestion(
    project: Project,
    section: DocumentSection,
    evidence: list[SearchResult],
    claim: DocumentClaim | None,
    ranked_sources: list[RankedSource],
) -> Suggestion:
    source = source_reference_for_claim(claim, ranked_sources, evidence[:3])
    original = claim.text if claim and claim.text in section.content else fragment(section.content)
    source_focus = strongest_source_focus(claim, ranked_sources, evidence)
    proposed = (
        "Reformular el fragmento como revision cientifica verificable: indicar que la idea requiere contraste "
        f"con {source_focus}, anadir fecha/contexto de vigencia y retirar cualquier afirmacion absoluta que no "
        "quede respaldada por una fuente concreta."
    )
    if claim:
        proposed = (
            f"Sustituir o matizar la afirmacion «{fragment(claim.text, 180)}» por una formulacion fechada y "
            f"atribuida a {source_focus}. Separar dato confirmado, interpretacion docente y aspecto pendiente "
            "de comprobacion antes de entrar en el tema final."
        )
    return Suggestion(
        project_id=project.id,
        section_id=section.id,
        suggestion_type=SuggestionType.scientific_update,
        original_fragment=original,
        proposed_change=proposed,
        justification=(
            "La propuesta se ha generado desde claims detectados en el documento y fuentes ordenadas por autoridad, "
            "vigencia y relevancia; no se integra sin revision docente."
        ),
        source_reference=source,
        confidence_level=confidence_from_sources(ranked_sources, fallback="medium" if evidence else "low"),
        status=SuggestionStatus.pending,
        anchor_context=build_anchor_context(section.content, original),
    )


def build_claim_curriculum_suggestion(
    project: Project,
    section: DocumentSection,
    official_evidence: list[SearchResult],
    all_evidence: list[SearchResult],
    claim: DocumentClaim | None,
    ranked_sources: list[RankedSource],
) -> Suggestion:
    usable = official_evidence or all_evidence
    source = source_reference_for_claim(claim, ranked_sources, usable[:3]) or project.legal_framework
    original = claim.text if claim and claim.text in section.content else fragment(section.content)
    source_focus = strongest_source_focus(claim, ranked_sources, usable)
    focus_fragment = f"«{fragment(claim.text, 180)}»" if claim else f"«{section.title}»"
    return Suggestion(
        project_id=project.id,
        section_id=section.id,
        suggestion_type=SuggestionType.legal_curricular,
        original_fragment=original,
        proposed_change=(
            f"Contrastar {focus_fragment} con {source_focus}. Incorporar solo competencias, criterios o saberes "
            "que el docente verifique en fuente oficial vigente; si no aparece el elemento exacto, dejarlo como "
            "pendiente de verificacion normativa."
        ),
        justification=(
            "La sugerencia curricular se basa en claims detectados y fuentes oficiales priorizadas. "
            f"Las fuentes genericas no bastan para consolidar normativa. Fuente prioritaria: {source_focus}. "
            f"Foco revisable: {focus_fragment}."
        ),
        source_reference=source,
        confidence_level=confidence_from_sources(ranked_sources, fallback="high" if official_evidence else "low"),
        status=SuggestionStatus.pending,
        anchor_context=build_anchor_context(section.content, original),
    )


def build_bibliographic_suggestion(
    project: Project,
    section: DocumentSection,
    evidence: list[SearchResult],
    rubric: AcademicRubricResult,
) -> Suggestion:
    source = format_source_reference(evidence[:3]) or "Sin evidencias externas suficientes."
    confidence = "medium" if evidence and rubric.academic_evidence_count > 0 else "low"
    proposed_change = (
        "Añadir una nota bibliográfica de revisión al final de la sección, diferenciando bibliografía base, "
        "fuentes oficiales y referencias científicas pendientes de comprobación docente."
    )
    if not evidence:
        proposed_change = (
            "Añadir una nota interna indicando que esta sección no debe presentarse como actualizada hasta "
            "incorporar bibliografía base o fuentes verificables aportadas por el profesor."
        )
    return Suggestion(
        project_id=project.id,
        section_id=section.id,
        suggestion_type=SuggestionType.bibliographic_update,
        original_fragment=fragment(section.content),
        proposed_change=proposed_change,
        justification=(
            "La trazabilidad bibliográfica es necesaria para distinguir actualización segura, sugerencia probable "
            "y aspecto que requiere verificación."
        ),
        source_reference=source,
        confidence_level=confidence,
        status=SuggestionStatus.pending,
        anchor_context=build_anchor_context(section.content, fragment(section.content)),
    )


def build_anchor_context(section_content: str, original_fragment: str) -> dict[str, str | bool]:
    clean_fragment = " ".join((original_fragment or "").split())
    clean_content = " ".join(section_content.split())
    index = clean_content.find(clean_fragment) if clean_fragment else -1
    if index == -1:
        return {"matched": False, "prefix": "", "suffix": ""}
    return {
        "matched": True,
        "prefix": clean_content[max(0, index - 80) : index],
        "suffix": clean_content[index + len(clean_fragment) : index + len(clean_fragment) + 80],
    }


def select_claim_for_types(claims: list[DocumentClaim], claim_types: set[ClaimType]) -> DocumentClaim | None:
    priority = {"high": 0, "medium": 1, "low": 2}
    candidates = [claim for claim in claims if claim.claim_type in claim_types]
    if not candidates:
        return None
    return sorted(candidates, key=lambda claim: priority.get(claim.review_priority, 9))[0]


def section_for_claim(sections: list[DocumentSection], claim: DocumentClaim) -> DocumentSection | None:
    return next((section for section in sections if section.id == claim.section_id), None)


def source_reference_for_claim(
    claim: DocumentClaim | None,
    ranked_sources: list[RankedSource],
    fallback: list[SearchResult],
) -> str:
    if claim:
        linked = [source for source in ranked_sources if claim.id in source.matched_claim_ids][:3]
        if linked:
            return "\n".join(
                f"{source.result.title}: {source.result.url} (score {source.total_score}/100, {source.validation_status})"
                for source in linked
            )
    return format_source_reference(fallback) or "Sin fuentes suficientes; requiere verificacion docente."


def strongest_source_focus(
    claim: DocumentClaim | None,
    ranked_sources: list[RankedSource],
    fallback: list[SearchResult],
) -> str:
    if claim:
        linked = [source for source in ranked_sources if claim.id in source.matched_claim_ids]
        if linked:
            best = sorted(linked, key=lambda source: source.total_score, reverse=True)[0]
            return f"{best.result.title} ({best.result.url}, score {best.total_score}/100)"
    if ranked_sources:
        best = ranked_sources[0]
        return f"{best.result.title} ({best.result.url}, score {best.total_score}/100)"
    if fallback:
        return f"{fallback[0].title} ({fallback[0].url})"
    return "fuentes verificables recuperadas por el sistema"


def confidence_from_sources(ranked_sources: list[RankedSource], fallback: str) -> str:
    if not ranked_sources:
        return fallback
    best = ranked_sources[0]
    if any(source.source_kind == "official" and source.total_score >= 55 for source in ranked_sources[:3]):
        return "high"
    if best.total_score >= 65:
        return "medium"
    return "low"


def extract_concept_terms(sections: list[DocumentSection]) -> list[str]:
    terms: list[str] = []
    for section in sections:
        if section.title:
            terms.append(section.title)
        for concept in section.detected_concepts or []:
            terms.append(str(concept))
    return [term.strip() for term in dict.fromkeys(terms) if term and term.strip()]


def expand_educational_level(level: str) -> str:
    lowered = normalize_query_text(level).lower()
    if "infantil" in lowered:
        return "Educación Infantil"
    if "primaria" in lowered:
        return "Educación Primaria"
    if "eso" in lowered or "secundaria" in lowered:
        return "Educación Secundaria Obligatoria"
    if "bachiller" in lowered:
        return "Bachillerato"
    if "fp" in lowered or "formacion profesional" in lowered:
        return "Formación Profesional"
    return level


def is_extremadura_context(text: str) -> bool:
    normalized = normalize_query_text(text).lower()
    return any(
        marker in normalized
        for marker in (
            "extremadura",
            "extremeno",
            "extremena",
            "juntaex",
            "educarex",
            "doe.juntaex",
            "decreto 98/2022",
            "decreto 107/2022",
            "decreto 109/2022",
            "decreto 110/2022",
            "decreto 14/2022",
            "ley 4/2011",
        )
    )


def unique_query_variants(queries: list[str]) -> list[str]:
    variants: list[str] = []
    for query in queries:
        variants.append(query)
        normalized = normalize_query_text(query)
        if normalized and normalized != query:
            variants.append(normalized)
    return [query for query in dict.fromkeys(variants) if query.strip()]


def normalize_query_text(text: str) -> str:
    without_marks = normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    cleaned = without_marks.replace("?", " ")
    return " ".join(cleaned.split())


def format_queries(queries: list[str]) -> str:
    if not queries:
        return "- Sin búsquedas configuradas."
    return "\n".join(f"- `{query}`" for query in queries)


def format_evidence(results: list[SearchResult]) -> str:
    if not results:
        return "- No se han encontrado fuentes suficientes. Requiere verificación manual."
    return "\n".join(result.as_markdown() for result in results)


def format_rubric_findings_for_report(rubric: AcademicRubricResult, codes: set[str]) -> str:
    selected = [finding for finding in rubric.findings if finding.code in codes]
    if not selected:
        return "- Sin riesgos automáticos específicos en esta dimensión."
    return "\n".join(
        (
            f"- **{finding.section_title}** · {finding.severity.upper()}: "
            f"{finding.message} Recomendación: {finding.recommendation}"
        )
        for finding in selected[:8]
    )


def format_evidence_for_prompt(results: list[SearchResult]) -> str:
    if not results:
        return "- Sin fuentes recuperadas."
    lines = []
    for result in results:
        snippet = " ".join(result.snippet.split())[:700]
        lines.append(f"- Título: {result.title}\n  URL: {result.url}\n  Extracto: {snippet}")
    return "\n".join(lines)


def format_source_reference(results: list[SearchResult]) -> str:
    return "\n".join(f"{result.title}: {result.url}" for result in results)


def fragment(text: str, limit: int = 420) -> str:
    clean = " ".join(text.split())
    return clean[:limit]


def is_official_source(url: str) -> bool:
    return is_official_url(url)


def is_available_evidence(result: SearchResult) -> bool:
    return "example.invalid" not in str(result.url)
