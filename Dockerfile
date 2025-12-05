FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && pip install --no-cache-dir uv \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./pyproject.toml
COPY README.md ./README.md
COPY src ./src

RUN uv pip install --system --no-cache .

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-m", "src.main"]

