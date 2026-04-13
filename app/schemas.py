from datetime import datetime
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    original_filename: str
    file_type: str
    total_chunks: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ChunkResponse(BaseModel):
    id: str
    document_id: str
    content: str
    chunk_index: int
    page_number: int | None
    score: float | None = None


class AskRequest(BaseModel):
    question: str
    document_ids: list[str] | None = None  # None = search all documents


class Source(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    page_number: int | None
    content_preview: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
