"""Embeddings via SiliconFlow API."""
import asyncio
from openai import AsyncOpenAI

from app.config import settings

_BATCH_SIZE = 16  # texts per request


def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.siliconflow_api_key,
        base_url="https://api.siliconflow.cn/v1",
    )


async def _embed_batch(texts: list[str]) -> list[list[float]]:
    response = await _get_client().embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    batches = [texts[i:i + _BATCH_SIZE] for i in range(0, len(texts), _BATCH_SIZE)]
    results = await asyncio.gather(*[_embed_batch(b) for b in batches])
    return [emb for batch in results for emb in batch]


async def embed_query(text: str) -> list[float]:
    embeddings = await embed_texts([text])
    return embeddings[0]
