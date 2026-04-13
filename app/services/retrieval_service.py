"""Vector similarity search using pgvector."""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import DocumentChunk, Document
from app.services.embedding_service import embed_query


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    content: str
    chunk_index: int
    page_number: int | None
    score: float  # cosine similarity (0-1, higher = more similar)


async def search(
    query: str,
    db: AsyncSession,
    top_k: int = 5,
    document_ids: list[str] | None = None,
) -> list[RetrievedChunk]:
    """Find the top-k most relevant chunks for a query."""
    query_vector = await embed_query(query)

    stmt = (
        select(
            DocumentChunk,
            (1 - DocumentChunk.embedding.cosine_distance(query_vector)).label("similarity"),
        )
        .options(selectinload(DocumentChunk.document))
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )

    if document_ids:
        stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

    rows = (await db.execute(stmt)).all()

    return [
        RetrievedChunk(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            filename=chunk.document.original_filename,
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            score=float(similarity),
        )
        for chunk, similarity in rows
    ]
