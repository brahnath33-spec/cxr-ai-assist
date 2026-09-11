Set-Location "C:\Users\brahn\cxr-ai-assist"
New-Item -ItemType Directory -Force -Path "backend\app\api\v1\endpoints" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\api\v1\schemas" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\api\v1\middleware" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\core" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\db" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\services" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\app\utils" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\tests\test_api" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\tests\test_core" | Out-Null
New-Item -ItemType Directory -Force -Path "backend\tests\test_integration" | Out-Null

# pyproject.toml
@'
[tool.poetry]
name = "cxrai-backend"
version = "1.0.0"
description = "CXR-AI Assist Backend API"
authors = ["Your Name <you@example.com>"]
packages = [{ include = "app" }]

[tool.poetry.dependencies]
python = ">=3.11,<3.13"
fastapi = "^0.109.0"
uvicorn = { extras = ["standard"], version = "^0.27.0" }
python-multipart = "^0.0.6"
sqlalchemy = "^2.0.25"
asyncpg = "^0.29.0"
alembic = "^1.13.1"
redis = "^5.0.1"
python-jose = { extras = ["cryptography"], version = "^3.3.0" }
passlib = { extras = ["bcrypt"], version = "^1.7.4" }
pydantic = "^2.5.3"
pydantic-settings = "^2.1.0"
python-dotenv = "^1.0.0"
structlog = "^24.1.0"
httpx = "^0.26.0"
tenacity = "^8.2.3"
boto3 = "^1.34.14"
prometheus-fastapi-instrumentator = "^6.1.0"
pillow = "^10.2.0"
numpy = "^1.26.3"

[tool.poetry.group.ml.dependencies]
torch = "^2.1.2"
torchvision = "^0.16.2"
onnxruntime = "^1.17.0"
opencv-python-headless = "^4.9.0.80"
pydicom = "^2.4.4"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.23.3"
pytest-cov = "^4.1.0"
httpx = "^0.26.0"
ruff = "^0.1.13"
mypy = "^1.8.0"
pre-commit = "^3.6.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "C4", "UP", "SIM"]
ignore = ["E501", "B008"]

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v"

[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/__init__.py"]
'@ | Out-File -FilePath "backend\pyproject.toml" -Encoding utf8

# config.py
@'
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
'@ | Out-File -FilePath "backend\app\config.py" -Encoding utf8

# logger.py
@'
"""Structured logging configuration."""

import logging
import sys
import structlog


def configure_logging(log_level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    return structlog.get_logger(name)
'@ | Out-File -FilePath "backend\app\utils\logger.py" -Encoding utf8

# health.py
@'
"""Health check endpoints."""

import time
from datetime import datetime, timezone

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(tags=["Health"])
START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    uptime_seconds: float
    timestamp: str


class ReadinessResponse(BaseModel):
    ready: bool
    checks: dict


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        uptime_seconds=round(time.time() - START_TIME, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/ready", response_model=ReadinessResponse, status_code=status.HTTP_200_OK)
async def readiness_check() -> ReadinessResponse:
    checks = {
        "database": "not_configured",
        "redis": "not_configured",
        "model_loaded": False,
    }
    return ReadinessResponse(ready=True, checks=checks)
'@ | Out-File -FilePath "backend\app\api\v1\endpoints\health.py" -Encoding utf8

# router.py
@'
"""Aggregate API v1 router."""

from fastapi import APIRouter
from app.api.v1.endpoints import health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
'@ | Out-File -FilePath "backend\app\api\v1\router.py" -Encoding utf8

# main.py
@'
"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import api_router
from app.config import get_settings
from app.utils.logger import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("application_starting", version=settings.APP_VERSION)
    yield
    logger.info("application_stopping")


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade clinical decision support for chest X-ray triage.",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    return JSONResponse({
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
    })


Instrumentator().instrument(app).expose(app, endpoint="/metrics")
'@ | Out-File -FilePath "backend\app\main.py" -Encoding utf8

# test_health.py
@'
"""Tests for health endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_check():
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert "ready" in response.json()


def test_openapi_docs():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "CXR-AI Assist"
'@ | Out-File -FilePath "backend\tests\test_api\test_health.py" -Encoding utf8

# Create __init__.py files
$dirs = @("backend\app", "backend\app\api", "backend\app\api\v1",
          "backend\app\api\v1\endpoints", "backend\app\api\v1\schemas",
          "backend\app\api\v1\middleware", "backend\app\core",
          "backend\app\db", "backend\app\services", "backend\app\utils",
          "backend\tests", "backend\tests\test_api")
foreach ($d in $dirs) {
    New-Item -ItemType File -Force -Path "$d\__init__.py" | Out-Null
}

Write-Host ""
Write-Host "=== BLOCK 2 COMPLETE ===" -ForegroundColor Green
Write-Host ""
Get-ChildItem -Recurse backend -File | Where-Object { $_.Extension -in ".py", ".toml" } | Select-Object FullName | Format-Table -AutoSize