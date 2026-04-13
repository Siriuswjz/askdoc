"""Parse documents and split into chunks."""
import io
from dataclasses import dataclass

import pdfplumber
from docx import Document as DocxDocument


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    page_number: int | None


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text into overlapping chunks, trying to break on paragraph/sentence boundaries."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            # Try to find a good break point (paragraph > sentence > word)
            for sep in ["\n\n", "\n", ". ", " "]:
                pos = text.rfind(sep, start + chunk_size // 2, end)
                if pos != -1:
                    end = pos + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - chunk_overlap

    return chunks


def parse_pdf(content: bytes, chunk_size: int, chunk_overlap: int) -> list[TextChunk]:
    chunks = []
    chunk_index = 0

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if not text:
                continue
            for part in _split_text(text, chunk_size, chunk_overlap):
                chunks.append(TextChunk(content=part, chunk_index=chunk_index, page_number=page_num))
                chunk_index += 1

    return chunks


def parse_docx(content: bytes, chunk_size: int, chunk_overlap: int) -> list[TextChunk]:
    doc = DocxDocument(io.BytesIO(content))
    full_text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    parts = _split_text(full_text, chunk_size, chunk_overlap)
    return [TextChunk(content=p, chunk_index=i, page_number=None) for i, p in enumerate(parts)]


def parse_txt(content: bytes, chunk_size: int, chunk_overlap: int) -> list[TextChunk]:
    text = content.decode("utf-8", errors="replace")
    parts = _split_text(text, chunk_size, chunk_overlap)
    return [TextChunk(content=p, chunk_index=i, page_number=None) for i, p in enumerate(parts)]


def parse_document(content: bytes, file_type: str, chunk_size: int, chunk_overlap: int) -> list[TextChunk]:
    parsers = {
        "pdf": parse_pdf,
        "docx": parse_docx,
        "txt": parse_txt,
    }
    parser = parsers.get(file_type.lower())
    if not parser:
        raise ValueError(f"Unsupported file type: {file_type}")
    return parser(content, chunk_size, chunk_overlap)
