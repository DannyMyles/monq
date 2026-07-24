from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_DIR / ".env"), extra="ignore")

    database_url: str = "mysql+pymysql://monq_user:monq_password@localhost:3306/monq"
    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-flash-lite-latest"
    gemini_embedding_model: str = "gemini-embedding-001"

    chunk_token_budget: int = 500
    chunk_token_overlap: int = 75

    rag_top_k: int = 5
    chat_history_turns: int = 3

    max_upload_mb: int = 20
    storage_dir: Path = BACKEND_DIR / "storage"

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings
