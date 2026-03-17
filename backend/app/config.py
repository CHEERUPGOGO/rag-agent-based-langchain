"""
Application configuration managed with pydantic-settings.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    openrouter_api_key: str = ""
    openrouter_model: str = "deepseek/deepseek-chat"
    default_provider: str = "openrouter"

    tavily_api_key: str = ""

    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "documents"
    metadata_db_path: str = "./metadata.db"
    checkpoint_db_path: str = "./checkpoint.db"
    upload_directory: str = "./uploads"

    log_directory: str = "./logs"
    log_level: str = "INFO"
    log_max_bytes: int = 10 * 1024 * 1024
    log_backup_count: int = 5

    embedding_model: str = "nomic-embed-text:latest"
    use_ollama_embeddings: bool = True
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text:latest"

    retrieval_top_k: int = 10
    rerank_top_k: int = 5

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()