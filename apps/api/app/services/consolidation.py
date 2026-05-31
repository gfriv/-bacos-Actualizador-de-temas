import re

from app.core.brand import (
    build_ai_notice,
    build_artifact_header,
    build_corporate_footer,
    generated_at_iso,
)
from app.db.models import DocumentSection, Suggestion, SuggestionStatus

ALLOWED_CONSOLIDATION_STATUSES = {SuggestionStatus.approved, SuggestionStatus.edited}


def build_consolidated_markdown(
    sections: list[DocumentSection],
    suggestions: list[Suggestion],
    *,
    project_title: str = "Proyecto Abacos",
    provider: str = "mock",
    model: str | None = None,
) -> str:
    approved = sorted(
        (suggestion for suggestion in suggestions if suggestion.status in ALLOWED_CONSOLIDATION_STATUSES),
        key=lambda suggestion: suggestion.id,
    )
    content_by_section = {section.id: section.content for section in sections}
    notes: list[str] = []

    for suggestion in approved:
        if suggestion.section_id and suggestion.section_id in content_by_section:
            current = content_by_section[suggestion.section_id]
            if _anchor_matches(current, suggestion):
                content_by_section[suggestion.section_id] = _replace_fragment(current, suggestion)
                suggestion.anchor_status = "matched"
                notes.append(_format_change_note(suggestion))
            else:
                suggestion.anchor_status = "failed"
                notes.append(
                    f"- Incidencia: sugerencia {suggestion.id} no integrada porque el fragmento original no encaja."
                )

    blocks: list[str] = [
        build_artifact_header(
            title="Documento consolidado",
            project_title=project_title,
            generated_at=generated_at_iso(),
            provider=provider,
            model=model,
        )
    ]
    for section in sorted(sections, key=lambda item: item.order_index):
        blocks.append(f"## {section.title}\n\n{content_by_section[section.id]}")

    if notes:
        blocks.append("## Notas internas de cambios\n\n" + "\n".join(notes))
    blocks.append(build_ai_notice())
    blocks.append(build_corporate_footer())

    return "\n\n".join(blocks)


def _anchor_matches(section_content: str, suggestion: Suggestion) -> bool:
    if suggestion.original_fragment not in section_content and not _fragment_pattern(suggestion).search(section_content):
        return False
    context = suggestion.anchor_context or {}
    if context.get("matched") is False:
        return False
    compact_content = " ".join(section_content.split())
    prefix = str(context.get("prefix") or "").strip()
    suffix = str(context.get("suffix") or "").strip()
    if prefix and prefix not in compact_content:
        return False
    if suffix and suffix not in compact_content:
        return False
    return True


def _replace_fragment(section_content: str, suggestion: Suggestion) -> str:
    if suggestion.original_fragment in section_content:
        return section_content.replace(suggestion.original_fragment, suggestion.proposed_change, 1)
    return _fragment_pattern(suggestion).sub(suggestion.proposed_change, section_content, count=1)


def _fragment_pattern(suggestion: Suggestion) -> re.Pattern[str]:
    tokens = suggestion.original_fragment.split()
    if not tokens:
        return re.compile(r"a^")
    return re.compile(r"\s+".join(re.escape(token) for token in tokens), re.IGNORECASE)


def _format_change_note(suggestion: Suggestion) -> str:
    return (
        f"- Sugerencia {suggestion.id}: {suggestion.suggestion_type.value}. "
        f"Antes: «{_compact(suggestion.original_fragment)}». "
        f"Después: «{_compact(suggestion.proposed_change)}»."
    )


def _compact(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else f"{compact[:limit]}..."
