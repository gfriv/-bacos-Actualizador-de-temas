from __future__ import annotations

from app.core.brand import build_ai_notice, build_artifact_header, build_corporate_footer
from app.services.report_quality_gate import assert_export_quality, evaluate_export_quality

REPAIRABLE_CODES = {
    "missing_brand_footer",
    "missing_ai_notice",
    "missing_generation_date",
    "missing_sources",
}


def ensure_exportable_markdown(
    content: str,
    *,
    artifact_type: str,
    title: str,
    project_title: str,
    require_sources: bool = False,
) -> tuple[str, bool]:
    try:
        assert_export_quality(content, artifact_type=artifact_type, require_sources=require_sources)
        return content, False
    except ValueError:
        result = evaluate_export_quality(
            content,
            artifact_type=artifact_type,
            require_sources=require_sources,
        )

    blocking_codes = {issue.code for issue in result.issues if issue.blocking}
    unsafe_codes = blocking_codes - REPAIRABLE_CODES
    if unsafe_codes:
        assert_export_quality(content, artifact_type=artifact_type, require_sources=require_sources)

    repaired = _repair_legacy_content(
        content,
        title=title,
        project_title=project_title,
        require_sources=require_sources,
        missing_codes={issue.code for issue in result.issues},
    )
    assert_export_quality(repaired, artifact_type=artifact_type, require_sources=require_sources)
    return repaired, True


def _repair_legacy_content(
    content: str,
    *,
    title: str,
    project_title: str,
    require_sources: bool,
    missing_codes: set[str],
) -> str:
    blocks: list[str] = []
    text = content.strip()
    if "missing_generation_date" in missing_codes or not text.startswith("#"):
        blocks.append(
            build_artifact_header(
                title=title,
                project_title=project_title,
                provider="compatibilidad",
                model="artefacto anterior",
            )
        )
    blocks.append(text)
    if require_sources and "missing_sources" in missing_codes:
        blocks.append(
            "## Fuentes y limitaciones\n\n"
            "- Este informe fue generado antes de la puerta de calidad actual y no conserva una referencia externa verificable.\n"
            "- Debe regenerarse antes de usarlo como base final en un piloto con documentacion real.\n"
            "- No se han inventado fuentes para reparar la descarga."
        )
    if "missing_ai_notice" in missing_codes:
        blocks.append(build_ai_notice())
    if "missing_brand_footer" in missing_codes:
        blocks.append(build_corporate_footer())
    return "\n\n".join(block for block in blocks if block)
