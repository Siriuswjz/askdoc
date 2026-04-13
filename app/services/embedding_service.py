"""Embeddings via SiliconFlow API."""
from openai import AsyncOpenAI

from app.config import settings


def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.siliconflow_api_key,
        base_url="https://api.siliconflow.cn/v1",
    )


async def embed_texts(texts: list[str]) -> list[list[float]]:
    response = await _get_client().embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


async def embed_query(text: str) -> list[float]:
    embeddings = await embed_texts([text])
    return embeddings[0]
