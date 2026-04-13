"""Document upload and management endpoints."""
import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Document, DocumentChunk
from app.schemas import DocumentResponse
from app.services import document_processor, embedding_service

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {"pdf", "docx", "txt"}


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    ext = Path(file.filename).suffix.lstrip(".").lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {ALLOWED_TYPES}")

    content = await file.read()
    if not content:
        raise HTTPException(400, "Empty file")

    # Parse & chunk
    try:
        text_chunks = document_processor.parse_document(
            content, ext, settings.chunk_size, settings.chunk_overlap
        )
    except Exception as e:
        raise HTTPException(422, f"Failed to parse document: {e}")

    if not text_chunks:
        raise HTTPException(422, "No text could be extracted from the document")

    # Embed all chunks
    texts = [c.content for c in text_chunks]
    embeddings = await embedding_service.embed_texts(texts)

    # Persist document + chunks
    doc = Document(
        original_filename=file.filename,
        file_type=ext,
        total_chunks=len(text_chunks),
    )
    db.add(doc)
    await db.flush()  # get doc.id before inserting chunks

    db_chunks = [
        DocumentChunk(
            document_id=doc.id,
            content=tc.content,
            chunk_index=tc.chunk_index,
            page_number=tc.page_number,
            embedding=emb,
        )
        for tc, emb in zip(text_chunks, embeddings)
    ]
    db.add_all(db_chunks)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    await db.delete(doc)
    await db.commit()
