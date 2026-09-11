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
