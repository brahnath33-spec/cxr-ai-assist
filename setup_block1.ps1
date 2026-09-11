Set-Location "C:\Users\brahn\cxr-ai-assist"

# .gitignore
@'
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# ML
*.pth
*.onnx
*.ckpt
mlruns/
wandb/

# Data
data/raw/*
data/processed/*
!data/raw/.gitkeep
!data/processed/.gitkeep

# Node
node_modules/
frontend/build/
frontend/dist/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Secrets
*.pem
*.key
kaggle.json

# DICOM
*.dcm
!tests/fixtures/*.dcm
'@ | Out-File -FilePath ".gitignore" -Encoding utf8

# .env.example
@'
APP_NAME=CXR-AI Assist
APP_ENV=development
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=INFO

API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

DATABASE_URL=postgresql+asyncpg://cxrai:cxrai@db:5432/cxrai
DATABASE_POOL_SIZE=10

REDIS_URL=redis://redis:6379/0
CACHE_TTL_SECONDS=3600

MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=cxrai-images

MODEL_PATH=/models/densenet121_chexpert.onnx
INFERENCE_BATCH_SIZE=1
USE_GPU=false
MAX_UPLOAD_SIZE_MB=50

CORS_ORIGINS=http://localhost:3000,http://localhost:80
'@ | Out-File -FilePath ".env.example" -Encoding utf8

# Makefile
@'
.PHONY: help install dev test lint format docker-up docker-down clean

help:
	@echo "Available commands: install, dev, test, lint, format, docker-up, docker-down, clean"

install:
	cd backend && poetry install

dev:
	cd backend && poetry run uvicorn app.main:app --reload --port 8000

test:
	cd backend && poetry run pytest --cov=app tests/

lint:
	cd backend && poetry run ruff check .

format:
	cd backend && poetry run ruff format .

docker-up:
	docker-compose -f docker/docker-compose.yml up -d --build

docker-down:
	docker-compose -f docker/docker-compose.yml down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
'@ | Out-File -FilePath "Makefile" -Encoding utf8

# .pre-commit-config.yaml
@'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ["--maxkb=1000"]
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
'@ | Out-File -FilePath ".pre-commit-config.yaml" -Encoding utf8

Write-Host ""
Write-Host "=== BLOCK 1 COMPLETE ===" -ForegroundColor Green
Write-Host ""
Get-ChildItem -File | Select-Object Name, Length | Format-Table -AutoSize