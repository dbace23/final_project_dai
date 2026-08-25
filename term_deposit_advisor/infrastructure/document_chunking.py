from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
import re

from pypdf import PdfReader


@dataclass(frozen=True)
class DocumentChunk:
    document_id: str
    document_name: str
    gcs_uri: str
    page: int
    chunk_id: str
    content: str
    created_at: str
    created_by: str


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    if chunk_size < 100:
        raise ValueError("Chunk size must be at least 100 characters.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Overlap must be zero or greater and smaller than chunk size.")
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def safe_document_id(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0].lower()
    value = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return value[:80] or "document"


def extract_pdf_chunks(
    pdf_bytes: bytes,
    *,
    document_id: str,
    document_name: str,
    source_uri: str,
    created_by: str,
    chunk_size: int,
    overlap: int,
) -> list[DocumentChunk]:
    if not document_id.strip():
        raise ValueError("Document ID is required.")
    if not document_name.strip():
        raise ValueError("Document name is required.")
    reader = PdfReader(BytesIO(pdf_bytes))
    created_at = datetime.now(timezone.utc).isoformat()
    rows: list[DocumentChunk] = []

    for page_number, page in enumerate(reader.pages, start=1):
        for chunk_number, content in enumerate(
            chunk_text(page.extract_text() or "", chunk_size, overlap),
            start=1,
        ):
            rows.append(
                DocumentChunk(
                    document_id=document_id,
                    document_name=document_name,
                    gcs_uri=source_uri,
                    page=page_number,
                    chunk_id=f"{document_id}_p{page_number}_c{chunk_number}",
                    content=content,
                    created_at=created_at,
                    created_by=created_by,
                )
            )
    return rows
