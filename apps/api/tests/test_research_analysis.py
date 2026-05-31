import pytest

from app.core.config import settings
from app.db.models import DocumentSection, Project
from app.research.schemas import SearchResult
from app.services.research_analysis import (
    build_research_analysis,
    is_official_source,
    official_curriculum_sources,
)


class FakeSearchProvider:
    name = "fake"

    async def search(self, query: str, max_results: int | None = None) -> list[SearchResult]:
        if "site:boe.es" in query:
            return [
                SearchResult(
                    title="BOE-A-2022 currículo básico",
                    url="https://www.boe.es/buscar/doc.php?id=BOE-A-2022-4975",
                    snippet="Normativa oficial de currículo básico para contraste.",
                    source="fake",
                )
            ]
        return [
            SearchResult(
                title="Artículo de revisión científica",
                url="https://example.edu/revision-cientifica",
                snippet="Evidencia científica reciente para contraste.",
                source="fake",
            )
        ]


@pytest.mark.anyio
async def test_research_analysis_uses_official_curriculum_evidence() -> None:
    project = Project(
        id=1,
        owner_id=1,
        title="Tema de prueba",
        area="Biología y Geología",
        educational_level="ESO",
        legal_framework="LOMLOE Real Decreto currículo básico",
    )
    section = DocumentSection(
        id=1,
        project_id=1,
        title="La célula",
        order_index=0,
        content="Contenido sobre célula, competencias y criterios de evaluación.",
        detected_concepts=["célula", "competencia científica"],
    )

    result = await build_research_analysis(project, [section], FakeSearchProvider())
    curriculum = next(item for item in result.suggestions if item.suggestion_type.value == "legal_curricular")

    assert len(result.reports) == 6
    assert len(result.suggestions) >= 2
    assert result.academic_score is not None
    assert any(report.report_type.value == "source_validation" for report in result.reports)
    assert all("Centro de Formación y Estudios Ábacos" in report.content_markdown for report in result.reports)
    assert all("asistencia de IA" in report.content_markdown for report in result.reports)
    assert "boe.es" in (curriculum.source_reference or "")
    assert curriculum.confidence_level == "high"


def test_extremadura_curriculum_sources_are_official_and_stage_aware() -> None:
    project = Project(
        id=2,
        owner_id=1,
        title="Tema de oposición de Infantil",
        area="Educación Infantil",
        educational_level="Oposiciones Educación Infantil",
        legal_framework="Extremadura LOMLOE Decreto 98/2022 convocatoria autonómica",
    )

    sources = official_curriculum_sources(project)
    urls = [url for _, url in sources]

    assert any("doe.juntaex.es" in url and "/98/" in url for url in urls)
    assert any("Ley 4/2011" in title for title, _ in sources)
    assert any("Orden de 9 de diciembre de 2022" in title for title, _ in sources)
    assert all(is_official_source(url) for url in urls)


@pytest.mark.anyio
async def test_research_analysis_fetches_curated_sources_without_general_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = Project(
        id=3,
        owner_id=1,
        title="Tema de Primaria",
        area="EducaciÃ³n Primaria",
        educational_level="Primaria",
        legal_framework="LOMLOE",
    )
    section = DocumentSection(
        id=3,
        project_id=3,
        title="Competencia cientÃ­fica",
        order_index=0,
        content="Contenido con competencias, criterios y saberes bÃ¡sicos.",
        detected_concepts=["competencias", "criterios"],
    )

    async def fake_curated_sources(project: Project) -> list[SearchResult]:
        return [
            SearchResult(
                title="BOE currÃ­culo Primaria",
                url="https://www.boe.es/buscar/act.php?id=BOE-A-2022-3296",
                snippet="Fuente oficial para contraste curricular.",
                source="BOE directo",
            )
        ]

    monkeypatch.setattr(settings, "official_source_fetch_enabled", True)
    monkeypatch.setattr("app.services.research_analysis.collect_curated_curriculum_evidence", fake_curated_sources)

    result = await build_research_analysis(project, [section], search_provider=None)

    assert result.official_sources_used is True
    assert result.web_search_used is False
    assert any("boe.es" in str(source.url) for source in result.evidence)
    curriculum = next(item for item in result.suggestions if item.suggestion_type.value == "legal_curricular")
    assert curriculum.confidence_level == "high"
