import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple

def extract_text_from_pdf(file_path: Path) -> str:
    """Extracts text content from PDF documents using pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(str(file_path))
        pages_text = []
        for idx, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                pages_text.append(f"<!-- Page {idx} -->\n{text}")
        return "\n\n".join(pages_text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF '{file_path}': {e}")

def extract_text_from_docx(file_path: Path) -> str:
    """Extracts text from DOCX documents using standard library zipfile and XML parsing."""
    try:
        with zipfile.ZipFile(file_path, "r") as z:
            xml_content = z.read("word/document.xml")
        root = ET.fromstring(xml_content)
        # XML namespace for WordprocessingML
        namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = []
        for p in root.iterfind(".//w:p", namespaces):
            texts = [node.text for node in p.iterfind(".//w:t", namespaces) if node.text]
            if texts:
                paragraphs.append("".join(texts))
        return "\n\n".join(paragraphs)
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX '{file_path}': {e}")

def load_document_file(file_path: Path | str) -> Tuple[str, dict]:
    """
    Ingests any document file (.md, .markdown, .txt, .pdf, .docx, .json).
    Returns (extracted_text, metadata_dict).
    """
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    meta = {
        "filename": path.name,
        "extension": suffix or "none",
        "size_bytes": path.stat().st_size,
    }

    if suffix in [".pdf"]:
        text = extract_text_from_pdf(path)
        meta["format"] = "PDF Document"
    elif suffix in [".docx"]:
        text = extract_text_from_docx(path)
        meta["format"] = "Microsoft Word (DOCX)"
    else:
        # Text-based formats (.md, .txt, .json, etc.)
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                text = path.read_text(encoding=encoding)
                meta["format"] = "Markdown / Plain Text"
                meta["encoding"] = encoding
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError(f"Could not decode text file {path} with common encodings.")

    meta["char_count"] = len(text)
    meta["line_count"] = len(text.splitlines())
    return text, meta
