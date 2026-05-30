from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

from app.research.schemas import SearchResult

SourceKind = Literal["official", "academic", "publisher", "generic", "unavailable"]
ValidationStatus = Literal["confirmed", "probable", "requires_verification"]

OFFICIAL_DOMAINS = (
    "boe.es",
    "doe.juntaex.es",
    "juntaex.es",
    "educarex.es",
    "educacionfpydeportes.gob.es",
    "educagob.educacionfpydeportes.gob.es",
    "todofp.es",
    "eur-lex.europa.eu",
    "europa.eu",
)

ACADEMIC_HINTS = (".edu", ".ac.", "revista", "journal", "doi.org", "scielo", "dialnet", "redalyc")
PUBLISHER_HINTS = ("springer", "elsevier", "wiley", "taylorfrancis", "sagepub", "mdpi")


@dataclass(frozen=True)
class EvidenceAssessment:
    title: str
    url: str
    source_kind: SourceKind
    score: int
    validation_status: ValidationStatus
    rationale: str


def is_official_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(domain in host for domain in OFFICIAL_DOMAINS)


def classify_source(result: SearchResult) -> SourceKind:
    url = str(result.url)
    if "example.invalid" in url:
        return "unavailable"
    host = urlparse(url).netloc.lower()
    haystack = f"{host} {result.title} {result.snippet}".lower()
    if is_official_url(url):
        return "official"
    if any(marker in haystack for marker in ACADEMIC_HINTS):
        return "academic"
    if any(marker in haystack for marker in PUBLISHER_HINTS):
        return "publisher"
    return "generic"


def assess_evidence(result: SearchResult) -> EvidenceAssessment:
    source_kind = classify_source(result)
    score = {
        "official": 95,
        "academic": 80,
        "publisher": 70,
        "generic": 45,
        "unavailable": 0,
    }[source_kind]
    validation_status: ValidationStatus = {
        "official": "confirmed",
        "academic": "probable",
        "publisher": "probable",
        "generic": "requires_verification",
        "unavailable": "requires_verification",
    }[source_kind]
    rationale = {
        "official": "Fuente oficial o normativa prioritaria para contraste curricular.",
        "academic": "Fuente académica útil, pero requiere lectura del documento completo.",
        "publisher": "Fuente editorial/científica útil, pendiente de revisión de acceso y pertinencia.",
        "generic": "Fuente no oficial; usar solo como orientación y verificar manualmente.",
        "unavailable": "No se pudo obtener evidencia suficiente.",
    }[source_kind]
    return EvidenceAssessment(
        title=result.title,
        url=str(result.url),
        source_kind=source_kind,
        score=score,
        validation_status=validation_status,
        rationale=rationale,
    )


def assess_evidence_list(results: list[SearchResult]) -> list[EvidenceAssessment]:
    return [assess_evidence(result) for result in results]


def validation_summary(results: list[SearchResult]) -> str:
    assessments = assess_evidence_list(results)
    if not assessments:
        return "Sin evidencias recuperadas. Requiere verificación docente."
    confirmed = sum(1 for item in assessments if item.validation_status == "confirmed")
    probable = sum(1 for item in assessments if item.validation_status == "probable")
    verify = sum(1 for item in assessments if item.validation_status == "requires_verification")
    return (
        f"Evidencias confirmadas: {confirmed}. "
        f"Sugerencias probables: {probable}. "
        f"Aspectos a verificar: {verify}."
    )


def format_assessments_markdown(results: list[SearchResult]) -> str:
    assessments = assess_evidence_list(results)
    if not assessments:
        return "- Sin fuentes evaluables."
    return "\n".join(
        (
            f"- **{item.title}** ({item.source_kind}, {item.score}/100, "
            f"{item.validation_status}): {item.rationale} [{item.url}]({item.url})"
        )
        for item in assessments
    )
