from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}


class UnsupportedDocumentTypeError(ValueError):
    pass


class UnreadableDocumentError(ValueError):
    pass


def parse_document(filename: str, content: bytes) -> tuple[str, dict[str, Any]]:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedDocumentTypeError(
            "Unsupported file type. Supported types are .md, .txt, and .pdf."
        )

    if extension == ".pdf":
        return _parse_pdf(content)

    text = content.decode("utf-8", errors="replace").strip()
    if not text:
        raise UnreadableDocumentError("Document is blank or contains no readable text.")

    return text, {
        "format": "Markdown / Text Document",
        "units_label": "lines",
        "count": len(text.splitlines()),
        "word_count": len(text.split()),
    }


def _parse_pdf(content: bytes) -> tuple[str, dict[str, Any]]:
    import pymupdf

    try:
        with pymupdf.open(stream=content, filetype="pdf") as document:
            page_count = len(document)
            is_slide_deck = bool(page_count and document[0].rect.width > document[0].rect.height)
            extracted_pages = []

            for index, page in enumerate(document):
                page_text = page.get_text("text", sort=True).strip()
                if page_text:
                    unit = "Slide" if is_slide_deck else "Page"
                    extracted_pages.append(f"=== [{unit} {index + 1}] ===\n{page_text}")
    except Exception as exc:
        raise UnreadableDocumentError("PDF could not be read.") from exc

    text = "\n\n".join(extracted_pages)
    if not text.strip():
        raise UnreadableDocumentError("Document is blank or contains no readable text.")

    return text, {
        "format": "PowerPoint Slide Deck (PDF)" if is_slide_deck else "Multi-Page PDF Document",
        "units_label": "slides" if is_slide_deck else "pages",
        "count": page_count,
        "word_count": len(text.split()),
    }
