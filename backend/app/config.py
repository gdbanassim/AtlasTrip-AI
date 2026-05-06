from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    frontend_origin: str = "http://localhost:3000"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"
    serpapi_api_key: str | None = None
    duffel_access_token: str | None = None
    liteapi_key: str | None = None
    geoapify_api_key: str | None = None
    opentripmap_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
