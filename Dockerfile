FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_NO_SYNC=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock README.md ./
COPY main.py ./

RUN uv sync --frozen --no-dev --no-install-project

ENTRYPOINT ["uv", "run", "main.py"]
