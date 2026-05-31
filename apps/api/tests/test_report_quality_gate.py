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


def test_quality_gate_does_not_block_spanish_todo_word() -> None:
    content = (
        valid_exportable_markdown()
        + "\n\nTodo el contenido, todos los apartados y todas las referencias deben revisarse por el docente."
    )

    assert evaluate_export_quality(content, artifact_type="report").ok is True


def test_quality_gate_does_not_block_academic_words_or_public_app_urls() -> None:
    content = (
        valid_exportable_markdown()
        + "\n\nLa hipótesis Null hypothesis aparece en una fuente anglosajona y no es un valor JSON."
        + "\nFuente pública: https://example.edu/app/revista-didactica"
    )

    result = evaluate_export_quality(content, artifact_type="report")

    assert result.ok is True
    assert "placeholder" not in {issue.code for issue in result.issues}
    assert "internal_path" not in {issue.code for issue in result.issues}


def test_quality_gate_blocks_uppercase_todo_placeholder() -> None:
    content = valid_exportable_markdown() + "\n\nTODO: completar referencias antes de exportar."

    result = evaluate_export_quality(content, artifact_type="report")

    assert result.ok is False
    assert "placeholder" in {issue.code for issue in result.issues}


@pytest.mark.parametrize(
    "technical_value",
    [
        "undefined",
        "null",
        "[object Object]",
        "CHANGE_ME",
        "dev-secret",
    ],
)
def test_quality_gate_blocks_technical_placeholders(technical_value: str) -> None:
    content = valid_exportable_markdown() + f"\n\nValor sin resolver: {technical_value}"

    result = evaluate_export_quality(content, artifact_type="report")

    assert result.ok is False
    assert "placeholder" in {issue.code for issue in result.issues}


@pytest.mark.parametrize(
    "internal_path",
    [
        r"C:\Users\doc\storage\uploads\tema.docx",
        "/app/storage/uploads/tema.docx",
        "/home/app/documento.pdf",
        "/tmp/abacos/documento.pdf",
        "apps/api/storage/uploads/tema.docx",
        "storage/generated/final.docx",
        "db://managed-file/123",
        "file_path",
        "docx_path",
    ],
)
def test_quality_gate_blocks_real_internal_paths(internal_path: str) -> None:
    content = valid_exportable_markdown() + f"\n\nRuta técnica: {internal_path}"

    result = evaluate_export_quality(content, artifact_type="report")

    assert result.ok is False
    assert "internal_path" in {issue.code for issue in result.issues}
