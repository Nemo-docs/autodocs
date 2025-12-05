FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && pip install --no-cache-dir uv \
    && rm -rf /var/lib/apt/lists/*

COPY main.py file_counter.py github_client.py pyproject.toml entrypoint.sh agents.py /action/

WORKDIR /action

RUN chmod +x /action/entrypoint.sh && \
    uv pip install --system --no-cache .

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/action/entrypoint.sh"]