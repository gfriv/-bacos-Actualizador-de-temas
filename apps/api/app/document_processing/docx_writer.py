from pathlib import Path

from docx import Document


def write_markdown_docx(markdown: str, path: str | Path) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    document = Document()

    for block in markdown.split("\n\n"):
        clean = block.strip()
        if not clean:
            continue
        if clean.startswith("# "):
            document.add_heading(clean.removeprefix("# "), level=1)
        elif clean.startswith("## "):
            document.add_heading(clean.removeprefix("## "), level=2)
        elif clean.startswith("- "):
            for item in clean.splitlines():
                document.add_paragraph(item.removeprefix("- "), style="List Bullet")
        else:
            document.add_paragraph(clean)

    document.save(target)
    return str(target)
