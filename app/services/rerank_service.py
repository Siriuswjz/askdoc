"""BGE-Reranker via SiliconFlow API."""
import httpx

from app.config import settings
from app.services.retrieval_service import RetrievedChunk


async def rerank(query: str, chunks: list[RetrievedChunk], top_n: int) -> list[RetrievedChunk]:
    """Re-score chunks with a cross-encoder and return top_n best matches."""
    if not chunks:
        return chunks

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.siliconflow.cn/v1/rerank",
            headers={
                "Authorization": f"Bearer {settings.siliconflow_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.rerank_model,
                "query": query,
                "documents": [c.content for c in chunks],
                "top_n": top_n,
                "return_documents": False,
            },
        )
        resp.raise_for_status()

    results = resp.json()["results"]
    # results is already sorted by relevance_score desc; each item has index + relevance_score
    reranked: list[RetrievedChunk] = []
    for item in results[:top_n]:
        original = chunks[item["index"]]
        reranked.append(
            RetrievedChunk(
                chunk_id=original.chunk_id,
                document_id=original.document_id,
                filename=original.filename,
                content=original.content,
                chunk_index=original.chunk_index,
                page_number=original.page_number,
                score=float(item["relevance_score"]),
            )
        )
    return reranked
