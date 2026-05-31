from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import EvidenceSource, Suggestion, SuggestionEvidence
from app.research.schemas import SearchResult
from app.research.source_policy import assess_evidence
from app.services.source_ranker import RankedSource


def build_evidence_sources(
    *,
    project_id: int,
    analysis_run_id: int | None,
    results: list[SearchResult],
    rankings: list[RankedSource] | None = None,
) -> list[EvidenceSource]:
    sources: list[EvidenceSource] = []
    seen: set[str] = set()
    ranking_by_url = {str(ranking.result.url): ranking for ranking in rankings or []}
    for result in results:
        url = str(result.url)
        if not url or url in seen or "example.invalid" in url:
            continue
        seen.add(url)
        assessment = assess_evidence(result)
        ranking = ranking_by_url.get(url)
        sources.append(
            EvidenceSource(
                project_id=project_id,
                analysis_run_id=analysis_run_id,
                title=result.title[:512],
                url=url[:2048],
                snippet=result.snippet,
                provider=result.source or "unknown",
                source_kind=ranking.source_kind if ranking else assessment.source_kind,
                validation_status=ranking.validation_status if ranking else assessment.validation_status,
                quality_score=ranking.total_score if ranking else assessment.score,
                rationale=_ranking_rationale(ranking) if ranking else assessment.rationale,
            )
        )
    return sources


def _ranking_rationale(ranking: RankedSource | None) -> str | None:
    if ranking is None:
        return None
    return (
        f"{ranking.rationale} "
        f"Scores: autoridad {ranking.authority_score}, vigencia {ranking.recency_score}, "
        f"legal {ranking.legal_relevance_score}, seccion {ranking.section_relevance_score}, "
        f"cita {ranking.citation_quality_score}."
    )


def link_suggestions_to_evidence(
    db: Session,
    *,
    suggestions: list[Suggestion],
    evidence_sources: list[EvidenceSource],
) -> None:
    if not suggestions or not evidence_sources:
        return
    for suggestion in suggestions:
        linked = _rank_evidence_for_suggestion(suggestion, evidence_sources)[:3]
        for source in linked:
            db.add(
                SuggestionEvidence(
                    suggestion=suggestion,
                    evidence_source=source,
                    relevance="primary" if source is linked[0] else "supporting",
                )
            )


def _rank_evidence_for_suggestion(
    suggestion: Suggestion,
    evidence_sources: list[EvidenceSource],
) -> list[EvidenceSource]:
    text = f"{suggestion.source_reference or ''} {suggestion.justification} {suggestion.proposed_change}".lower()
    scored: list[tuple[int, EvidenceSource]] = []
    for source in evidence_sources:
        score = source.quality_score
        if source.url.lower() in text:
            score += 80
        if source.title.lower()[:40] and source.title.lower()[:40] in text:
            score += 30
        if suggestion.suggestion_type.value == "legal_curricular" and source.source_kind == "official":
            score += 25
        if suggestion.suggestion_type.value == "scientific_update" and source.source_kind in {"academic", "publisher"}:
            score += 20
        scored.append((score, source))
    return [source for _, source in sorted(scored, key=lambda item: item[0], reverse=True)]
