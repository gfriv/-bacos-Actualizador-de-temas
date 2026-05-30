from app.research.schemas import SearchResult
from app.research.source_policy import assess_evidence, format_assessments_markdown, is_official_url


def test_source_policy_prioritizes_official_extremadura_sources() -> None:
    result = SearchResult(
        title="DOE currículo Extremadura",
        url="https://doe.juntaex.es/eli/es-ex/d/2022/07/28/107/con",
        snippet="Currículo de Educación Primaria para Extremadura.",
        source="direct",
    )

    assessment = assess_evidence(result)

    assert is_official_url(str(result.url))
    assert assessment.source_kind == "official"
    assert assessment.validation_status == "confirmed"
    assert assessment.score >= 90


def test_source_policy_marks_generic_sources_for_human_verification() -> None:
    result = SearchResult(
        title="Blog educativo",
        url="https://example.com/blog/curriculo",
        snippet="Resumen no oficial.",
        source="search",
    )

    assessment = assess_evidence(result)
    rendered = format_assessments_markdown([result])

    assert assessment.source_kind == "generic"
    assert assessment.validation_status == "requires_verification"
    assert "requires_verification" in rendered
