import pytest

from app.core.brand import build_ai_notice, build_artifact_header, build_corporate_footer
from app.services.report_quality_gate import assert_export_quality, evaluate_export_quality


def valid_exportable_markdown() -> str:
    return "\n\n".join(
        [
            build_artifact_header(
                title="Informe de prueba",
                project_title="Tema de prueba",
                generated_at="2026-05-30 10:00 UTC",
                provider="mock",
                model="MockProvider",
            ),
            "## Fuentes\n\n- Fuente oficial: https://www.boe.es/",
            build_ai_notice(),
            build_corporate_footer(),
        ]
    )


def test_quality_gate_accepts_traceable_export() -> None:
    result = evaluate_export_quality(
        valid_exportable_markdown(),
        artifact_type="scientific_update",
        require_sources=True,
    )

    assert result.ok is True
    assert result.score >= 80


def test_quality_gate_blocks_internal_paths_and_secrets() -> None:
    content = valid_exportable_markdown() + "\n\nC:\\Users\\doc\\storage\\uploads\\tema.docx\nsk-test-secret-secret"

    result = evaluate_export_quality(content, artifact_type="report")

    assert result.ok is False
    assert {issue.code for issue in result.issues} >= {"secret_like_value", "internal_path"}
    with pytest.raises(ValueError):
        assert_export_quality(content, artifact_type="report")
