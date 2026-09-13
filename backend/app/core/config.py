from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "SIH 2026 E-Waste Platform"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    mock_otp_enabled: bool = True
    app_secret_key: str = "dev-only-change-me"
    access_token_ttl_seconds: int = 86400

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
