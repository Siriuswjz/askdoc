from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    siliconflow_api_key: str = ""
    database_url: str = "postgresql+asyncpg://raguser:ragpassword@localhost:5432/ragdb"

    @property
    def async_database_url(self) -> str:
        """Normalize Railway/Render postgres:// → postgresql+asyncpg://"""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    upload_dir: str = "./uploads"
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    chunk_size: int = 800
    chunk_overlap: int = 100
    retrieval_top_k: int = 5
    retrieval_candidates: int = 20   # candidates fetched before reranking
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    use_rerank: bool = True
    conversation_history_limit: int = 10  # max past messages sent to LLM

    class Config:
        env_file = ".env"


settings = Settings()
