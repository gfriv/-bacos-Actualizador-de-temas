from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./abacos.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = Field(default="dev-secret-change-me")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8
    storage_backend: str = "local"
    upload_dir: str = "./storage/uploads"
    generated_dir: str = "./storage/generated"
    max_upload_mb: int = 50
    ocr_enabled: bool = False
    ocr_languages: str = "spa+eng"
    ocr_dpi: int = 200
    ocr_max_pages: int = 40
    ocr_timeout_seconds: int = 30
    ocr_tesseract_cmd: str = ""
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    llm_provider: str = "mock"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_pull_enabled: bool = False
    analysis_llm_enabled: bool = False
    external_ai_providers_enabled: bool = False
    external_ai_data_processing_confirmed: bool = False
    web_search_provider: str = "disabled"
    external_web_search_enabled: bool = False
    web_search_max_results: int = 5
    web_search_timeout_seconds: float = 6.0
    tavily_api_key: str = ""
    brave_search_api_key: str = ""
    demo_access_enabled: bool = True
    demo_user_email: str = "demo@abacos.test"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
