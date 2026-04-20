"""SiliconFlow-powered Q&A (DeepSeek-R1-Distill-Qwen-7B)."""
from openai import AsyncOpenAI

from app.config import settings
from app.schemas import AskResponse, Source
from app.services.retrieval_service import RetrievedChunk, search

_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"

_SYSTEM_PROMPT = """You are an enterprise document Q&A assistant. Answer questions \
accurately based on the provided document context only.
- If the context does not contain sufficient information, say so explicitly
- Always cite sources (document name and page number when available)
- Be concise and professional"""


def _get_client() -> AsyncOpenAI:
    if not settings.siliconflow_api_key:
        from fastapi import HTTPException
        raise HTTPException(500, "SILICONFLOW_API_KEY is not configured. Add it to your .env file.")
    return AsyncOpenAI(
        api_key=settings.siliconflow_api_key,
        base_url="https://api.siliconflow.cn/v1",
    )


def _format_chunks(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for c in chunks:
        source = f"[{c.filename}"
        if c.page_number:
            source += f", page {c.page_number}"
        source += "]"
        parts.append(f"{source}\n{c.content}")
    return "\n\n---\n\n".join(parts)


def _chunks_to_sources(chunks: list[RetrievedChunk]) -> list[Source]:
    seen = set()
    sources = []
    for c in chunks:
        key = (c.document_id, c.chunk_index)
        if key not in seen:
            seen.add(key)
            sources.append(
                Source(
                    document_id=c.document_id,
                    filename=c.filename,
                    chunk_index=c.chunk_index,
                    page_number=c.page_number,
                    content_preview=c.content[:200] + ("..." if len(c.content) > 200 else ""),
                )
            )
    return sources


async def answer_question(
    question: str,
    db,
    document_ids: list[str] | None = None,
) -> AskResponse:
    chunks = await search(question, db, top_k=settings.retrieval_top_k, document_ids=document_ids)

    response = await _get_client().chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Document context:\n\n{_format_chunks(chunks)}\n\nQuestion: {question}",
            },
        ],
        max_tokens=2048,
    )

    import re
    raw = response.choices[0].message.content or "I was unable to generate an answer."
    answer = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    return AskResponse(answer=answer, sources=_chunks_to_sources(chunks))
