import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedSection:
    title: str
    order_index: int
    content: str
    summary: str
    detected_concepts: list[str]


HEADING_RE = re.compile(r"^(#{1,3}\s+.+|\d+[\).]\s+.+|[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{8,})$")


def split_sections(text: str) -> list[ParsedSection]:
    lines = [line.strip() for line in text.splitlines()]
    sections: list[tuple[str, list[str]]] = []
    current_title = "Introducción"
    current_lines: list[str] = []

    for line in lines:
        if not line:
            continue
        if HEADING_RE.match(line) and current_lines:
            sections.append((current_title, current_lines))
            current_title = line.lstrip("# ").strip()
            current_lines = []
        elif HEADING_RE.match(line) and not current_lines:
            current_title = line.lstrip("# ").strip()
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    if not sections and text.strip():
        sections.append(("Introducción", [text.strip()]))

    return [
        ParsedSection(
            title=title,
            order_index=index,
            content="\n\n".join(content_lines),
            summary=_summarize(content_lines),
            detected_concepts=_detect_concepts(content_lines),
        )
        for index, (title, content_lines) in enumerate(sections, start=1)
    ]


def _summarize(lines: list[str]) -> str:
    joined = " ".join(lines)
    return joined[:220] + ("..." if len(joined) > 220 else "")


def _detect_concepts(lines: list[str]) -> list[str]:
    text = " ".join(lines).lower()
    candidates = [
        "competencias",
        "criterios",
        "saberes",
        "evaluación",
        "metodología",
        "currículo",
        "legislación",
        "bibliografía",
    ]
    return [concept for concept in candidates if concept in text]
