"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "CXR-AI Assist"
    APP_ENV: str = "development"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    DATABASE_URL: str = "postgresql+asyncpg://cxrai:cxrai@db:5432/cxrai"
    DATABASE_POOL_SIZE: int = 10

    REDIS_URL: str = "redis://redis:6379/0"
    CACHE_TTL_SECONDS: int = 3600

    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "cxrai-images"

    MODEL_PATH: str = "/models/densenet121_chexpert.onnx"
    CHECKPOINT_PATH: str = "ml/models/best_densenet121_chexpert.pth"
    INFERENCE_BATCH_SIZE: int = 1
    USE_GPU: bool = False
    MAX_UPLOAD_SIZE_MB: int = 50

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:80"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
