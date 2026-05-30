from app.db.models import DocumentSection, Suggestion, SuggestionStatus

ALLOWED_CONSOLIDATION_STATUSES = {SuggestionStatus.approved, SuggestionStatus.edited}


def build_consolidated_markdown(
    sections: list[DocumentSection],
    suggestions: list[Suggestion],
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
            if suggestion.original_fragment in current:
                content_by_section[suggestion.section_id] = current.replace(
                    suggestion.original_fragment, suggestion.proposed_change, 1
                )
            else:
                content_by_section[suggestion.section_id] = (
                    current
                    + "\n\n"
                    + f"Nota de actualización aprobada: {suggestion.proposed_change}"
                )
            notes.append(f"- Sugerencia {suggestion.id}: {suggestion.suggestion_type.value}")

    blocks: list[str] = ["# Documento consolidado"]
    for section in sorted(sections, key=lambda item: item.order_index):
        blocks.append(f"## {section.title}\n\n{content_by_section[section.id]}")

    if notes:
        blocks.append("## Notas internas de cambios\n\n" + "\n".join(notes))

    return "\n\n".join(blocks)
