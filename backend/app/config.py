from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_work_os"
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24
    openai_api_key: str = ""
    openai_text_model: str = "gpt-5-mini"
    openai_transcribe_model: str = "gpt-4o-transcribe"
    openai_embedding_model: str = "text-embedding-3-small"
    upload_dir: Path = Path("./storage")
    frontend_url: str = "http://localhost:3000"
    demo_ai_enabled: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
