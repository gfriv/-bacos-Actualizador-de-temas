import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedSection:
    title: str
    order_index: int
    content: str
    summary: str
    detected_concepts: list[str]


MAX_SECTION_CHARS = 9000
MARKDOWN_HEADING_RE = re.compile(r"^(#{1,4})\s+(.{2,160})$")
NUMBERED_HEADING_RE = re.compile(r"^\d+(?:\.\d+)*[\).]?\s+.{3,160}$")
THEME_HEADING_RE = re.compile(
    r"^(tema|unidad|bloque|apartado|capitulo|capítulo|modulo|módulo)\s+[\w\dIVXLCDM]+[\).:\-\s].{2,160}$",
    re.IGNORECASE,
)
ALL_CAPS_RE = re.compile(r"^[A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ0-9\s,;:()\-]{8,160}$")
PAGE_MARKER_RE = re.compile(r"^\[p[áa]gina\s+\d+\]$", re.IGNORECASE)
TABLE_ROW_RE = re.compile(r"^\|.+\|$")


def split_sections(text: str) -> list[ParsedSection]:
    lines = [_normalize_line(line) for line in text.splitlines()]
    raw_sections: list[tuple[str, list[str]]] = []
    current_title = "Introducción"
    current_lines: list[str] = []

    for line in lines:
        if not line:
            continue
        heading = _extract_heading_title(line)
        if heading and current_lines:
            raw_sections.append((current_title, current_lines))
            current_title = heading
            current_lines = []
        elif heading and not current_lines:
            current_title = heading
        else:
            current_lines.append(line)

    if current_lines:
        raw_sections.append((current_title, current_lines))

    if not raw_sections and text.strip():
        raw_sections.append(("Introducción", [text.strip()]))

    expanded_sections: list[tuple[str, list[str]]] = []
    for title, content_lines in raw_sections:
        expanded_sections.extend(_chunk_section(title, content_lines))

    return [
        ParsedSection(
            title=title,
            order_index=index,
            content="\n\n".join(content_lines),
            summary=_summarize(content_lines),
            detected_concepts=_detect_concepts(title, content_lines),
        )
        for index, (title, content_lines) in enumerate(expanded_sections, start=1)
    ]


def _extract_heading_title(line: str) -> str | None:
    if TABLE_ROW_RE.match(line) or PAGE_MARKER_RE.match(line):
        return None
    markdown_match = MARKDOWN_HEADING_RE.match(line)
    if markdown_match:
        return markdown_match.group(2).strip()
    if NUMBERED_HEADING_RE.match(line) or THEME_HEADING_RE.match(line):
        return line.strip()
    if ALL_CAPS_RE.match(line) and _letter_count(line) >= 8:
        return line.title()
    return None


def _chunk_section(title: str, lines: list[str]) -> list[tuple[str, list[str]]]:
    content = "\n\n".join(lines)
    if len(content) <= MAX_SECTION_CHARS:
        return [(title, lines)]

    chunks: list[tuple[str, list[str]]] = []
    current: list[str] = []
    current_size = 0
    for line in lines:
        line_size = len(line) + 2
        if current and current_size + line_size > MAX_SECTION_CHARS:
            chunks.append((_part_title(title, len(chunks) + 1), current))
            current = []
            current_size = 0
        current.append(line)
        current_size += line_size
    if current:
        chunks.append((_part_title(title, len(chunks) + 1), current))
    return chunks


def _part_title(title: str, part_number: int) -> str:
    return title if part_number == 1 else f"{title} (parte {part_number})"


def _summarize(lines: list[str]) -> str:
    joined = " ".join(lines)
    return joined[:220] + ("..." if len(joined) > 220 else "")


def _detect_concepts(title: str, lines: list[str]) -> list[str]:
    text = f"{title} {' '.join(lines)}".lower()
    candidates = [
        "competencias",
        "criterios",
        "saberes",
        "evaluación",
        "metodología",
        "currículo",
        "curricular",
        "legislación",
        "normativa",
        "bibliografía",
        "oposiciones",
        "infantil",
        "primaria",
        "secundaria",
        "bachillerato",
        "formación profesional",
        "extremadura",
    ]
    return [concept for concept in candidates if concept in text]


def _normalize_line(line: str) -> str:
    return " ".join(line.replace("\t", " ").split())


def _letter_count(line: str) -> int:
    return sum(1 for char in line if char.isalpha())
