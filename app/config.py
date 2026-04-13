from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    siliconflow_api_key: str = ""
    database_url: str = "postgresql+asyncpg://raguser:ragpassword@localhost:5432/ragdb"
    upload_dir: str = "./uploads"
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    chunk_size: int = 800
    chunk_overlap: int = 100
    retrieval_top_k: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
