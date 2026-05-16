FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ARG GWS_VERSION=v0.22.5
ARG TARGETARCH

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_NO_SYNC=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
  && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) GWS_ARCH=x86_64 ;; \
      arm64) GWS_ARCH=aarch64 ;; \
      *) echo "unsupported TARGETARCH=${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    curl -fsSL -o /tmp/google-workspace-cli-${GWS_ARCH}-unknown-linux-gnu.tar.gz "https://github.com/googleworkspace/cli/releases/download/${GWS_VERSION}/google-workspace-cli-${GWS_ARCH}-unknown-linux-gnu.tar.gz"; \
    curl -fsSL -o /tmp/google-workspace-cli-${GWS_ARCH}-unknown-linux-gnu.tar.gz.sha256 "https://github.com/googleworkspace/cli/releases/download/${GWS_VERSION}/google-workspace-cli-${GWS_ARCH}-unknown-linux-gnu.tar.gz.sha256"; \
    (cd /tmp && sha256sum -c google-workspace-cli-${GWS_ARCH}-unknown-linux-gnu.tar.gz.sha256); \
    tar -xzf /tmp/google-workspace-cli-${GWS_ARCH}-unknown-linux-gnu.tar.gz -C /usr/local/bin ./gws; \
    chmod 0755 /usr/local/bin/gws; \
    rm -f /tmp/google-workspace-cli-${GWS_ARCH}-unknown-linux-gnu.tar.gz /tmp/google-workspace-cli-${GWS_ARCH}-unknown-linux-gnu.tar.gz.sha256; \
    gws --version

COPY pyproject.toml uv.lock README.md ./
COPY main.py prompts.py ./
COPY .claude/skills ./.claude/skills

RUN uv sync --frozen --no-dev --no-install-project
RUN useradd --create-home --home-dir /home/appuser --uid 10001 appuser && chown -R appuser:appuser /app /home/appuser

USER appuser

ENTRYPOINT ["uv", "run", "main.py"]
CMD ["--log-level", "INFO"]
