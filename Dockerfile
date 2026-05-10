FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_NO_SYNC=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/appuser

COPY pyproject.toml uv.lock README.md ./
COPY main.py ./

RUN uv sync --frozen --no-dev --no-install-project
RUN useradd --create-home --home-dir /home/appuser --uid 10001 appuser && chown -R appuser:appuser /app /home/appuser

USER appuser

ENTRYPOINT ["uv", "run", "main.py"]
