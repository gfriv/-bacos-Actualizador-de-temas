from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from app.db.models import Project
from app.research.schemas import SearchResult
from app.research.source_policy import assess_evidence
from app.services.claim_extractor import ClaimType, DocumentClaim


@dataclass(frozen=True)
class RankedSource:
    result: SearchResult
    source_kind: str
    validation_status: str
    authority_score: int
    recency_score: int
    legal_relevance_score: int
    section_relevance_score: int
    citation_quality_score: int
    total_score: int
    matched_claim_ids: tuple[str, ...]
    rationale: str


YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")


def rank_sources_for_claims(
    results: list[SearchResult],
    claims: list[DocumentClaim],
    project: Project,
) -> list[RankedSource]:
    ranked = [_rank_source(result, claims, project) for result in results if "example.invalid" not in str(result.url)]
    return sorted(ranked, key=lambda item: item.total_score, reverse=True)


def format_ranked_sources_markdown(sources: list[RankedSource], limit: int = 10) -> str:
    if not sources:
        return "- Sin fuentes puntuables."
    return "\n".join(
        (
            f"- **{source.result.title}** · {source.source_kind} · {source.total_score}/100 "
            f"(autoridad {source.authority_score}, vigencia {source.recency_score}, "
            f"relevancia {source.section_relevance_score}). {source.rationale} [{source.result.url}]({source.result.url})"
        )
        for source in sources[:limit]
    )


def _rank_source(result: SearchResult, claims: list[DocumentClaim], project: Project) -> RankedSource:
    assessment = assess_evidence(result)
    text = _normalize(f"{result.title} {result.snippet} {result.url}")
    project_text = _normalize(f"{project.area} {project.educational_level} {project.legal_framework}")
    matched_claims = _matched_claims(text, claims)
    authority_score = assessment.score
    recency_score = _recency_score(text)
    legal_score = _legal_relevance_score(text, project_text, matched_claims)
    section_score = _section_relevance_score(text, matched_claims)
    citation_score = _citation_quality_score(text)
    total = round(
        authority_score * 0.38
        + recency_score * 0.14
        + legal_score * 0.2
        + section_score * 0.2
        + citation_score * 0.08
    )
    return RankedSource(
        result=result,
        source_kind=assessment.source_kind,
        validation_status=assessment.validation_status,
        authority_score=authority_score,
        recency_score=recency_score,
        legal_relevance_score=legal_score,
        section_relevance_score=section_score,
        citation_quality_score=citation_score,
        total_score=max(0, min(100, total)),
        matched_claim_ids=tuple(claim.id for claim in matched_claims),
        rationale=_rationale(assessment.source_kind, matched_claims, legal_score, recency_score),
    )


def _matched_claims(text: str, claims: list[DocumentClaim]) -> list[DocumentClaim]:
    matches: list[DocumentClaim] = []
    for claim in claims:
        term_hits = sum(1 for term in claim.search_terms if _normalize(term) in text)
        trigger_hits = sum(1 for term in claim.trigger_terms if _normalize(term) in text)
        if term_hits >= 2 or trigger_hits:
            matches.append(claim)
    return matches


def _recency_score(text: str) -> int:
    current_year = datetime.now(UTC).year
    years = [int(match.group(1)) for match in YEAR_PATTERN.finditer(text)]
    if not years:
        return 55
    newest = max(years)
    if newest >= current_year - 2:
        return 95
    if newest >= current_year - 5:
        return 80
    if newest >= current_year - 10:
        return 60
    return 35


def _legal_relevance_score(text: str, project_text: str, matched_claims: list[DocumentClaim]) -> int:
    score = 20
    if any(claim.claim_type in {ClaimType.legal, ClaimType.curricular} for claim in matched_claims):
        score += 25
    for marker in ("boe.es", "doe.juntaex.es", "educarex", "real decreto", "decreto", "orden", "lomloe"):
        if marker in text:
            score += 10
    if "extremadura" in project_text and ("doe.juntaex" in text or "extremadura" in text):
        score += 20
    if "oposicion" in project_text and ("convocatoria" in text or "276/2007" in text):
        score += 20
    return min(score, 100)


def _section_relevance_score(text: str, matched_claims: list[DocumentClaim]) -> int:
    if not matched_claims:
        return 30
    priority_bonus = {"high": 20, "medium": 10, "low": 0}
    score = 45 + min(35, len(matched_claims) * 12)
    score += max(priority_bonus.get(claim.review_priority, 0) for claim in matched_claims)
    return min(score, 100)


def _citation_quality_score(text: str) -> int:
    score = 35
    for marker in ("doi", "isbn", "boe-a-", "eli/", "revista", "journal", "pdf"):
        if marker in text:
            score += 12
    return min(score, 100)


def _rationale(kind: str, matched_claims: list[DocumentClaim], legal_score: int, recency_score: int) -> str:
    parts = [f"Clasificada como {kind}."]
    if matched_claims:
        parts.append(f"Relacionada con {len(matched_claims)} afirmacion(es) del documento.")
    if legal_score >= 75:
        parts.append("Alta pertinencia normativa.")
    if recency_score < 50:
        parts.append("Vigencia temporal limitada; requiere revision.")
    return " ".join(parts)


def _normalize(text: object) -> str:
    replacements = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return " ".join(str(text).translate(replacements).lower().split())
