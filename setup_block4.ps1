Set-Location "C:\Users\brahn\cxr-ai-assist"
New-Item -ItemType Directory -Force -Path "docker" | Out-Null
New-Item -ItemType Directory -Force -Path "infra\nginx" | Out-Null
New-Item -ItemType Directory -Force -Path ".github\workflows" | Out-Null

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

# Dockerfile.api
$dockerfileApi = @'
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.7.1

COPY backend/pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --without ml,dev

FROM python:3.11-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY backend/app ./app

RUN useradd -m -u 1000 cxrai && chown -R cxrai:cxrai /app
USER cxrai

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'@
[System.IO.File]::WriteAllText("$PWD\docker\Dockerfile.api", $dockerfileApi, $utf8NoBom)

# Dockerfile.frontend
$dockerfileFrontend = @'
FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
'@
[System.IO.File]::WriteAllText("$PWD\docker\Dockerfile.frontend", $dockerfileFrontend, $utf8NoBom)

# docker-compose.yml
$dockerCompose = @'
version: '3.9'

services:
  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    container_name: cxrai-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://cxrai:cxrai@db:5432/cxrai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - cxrai-network
    restart: unless-stopped

  frontend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.frontend
    container_name: cxrai-frontend
    ports:
      - "3000:80"
    depends_on:
      - api
    networks:
      - cxrai-network
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    container_name: cxrai-db
    environment:
      POSTGRES_USER: cxrai
      POSTGRES_PASSWORD: cxrai
      POSTGRES_DB: cxrai
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cxrai"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cxrai-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: cxrai-redis
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cxrai-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  cxrai-network:
    driver: bridge
'@
[System.IO.File]::WriteAllText("$PWD\docker\docker-compose.yml", $dockerCompose, $utf8NoBom)

# nginx.conf
$nginxConf = @'
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        client_max_body_size 50M;

        location /api/ {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 300s;
        }
    }
}
'@
[System.IO.File]::WriteAllText("$PWD\infra\nginx\nginx.conf", $nginxConf, $utf8NoBom)

# CI workflow
$ciYml = @'
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Poetry
        run: pip install poetry==1.7.1
      - name: Install dependencies
        working-directory: backend
        run: poetry install --without ml --no-root
      - name: Run tests
        working-directory: backend
        run: poetry run pytest

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install and build
        working-directory: frontend
        run: npm install && npm run build
'@
[System.IO.File]::WriteAllText("$PWD\.github\workflows\ci.yml", $ciYml, $utf8NoBom)

Write-Host ""
Write-Host "=== BLOCK 4 COMPLETE ===" -ForegroundColor Green
Get-ChildItem -Recurse docker, infra, .github -File | Select-Object FullName | Format-Table -AutoSize