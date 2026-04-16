# ── Build stage ───────────────────────────────────────────────────────────────
# Installs dependencies into a virtualenv using uv.
# Kept separate so the final image never contains build tools or the uv binary.
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /bin/

WORKDIR /code

# Workspace-level lockfile and root pyproject needed for uv workspace resolution.
COPY pyproject.toml uv.lock ./

# App source and shared common libraries.
COPY apps/sample/ ./apps/sample/
COPY common/ ./common/

# Install into an isolated venv under /code/.venv.
RUN uv sync --package sample --frozen --no-cache

# ── Runtime stage ─────────────────────────────────────────────────────────────
# Copies only the venv and app source — no build tooling, no uv binary.
FROM python:${PYTHON_VERSION}-slim AS runtime

WORKDIR /code

# Copy the pre-built venv from the builder stage.
COPY --from=builder /code/.venv /code/.venv

# Copy the app source and shared libs (needed at runtime for imports).
COPY --from=builder /code/apps/sample/ ./apps/sample/
COPY --from=builder /code/common/ ./common/

# Python resolution: app module directory + common lib src trees.
ENV PYTHONPATH=/code/apps/sample:/code/common/libs/models/src:/code/common/libs/fastapi/src:/code/common/libs/fdebenchkit/src
ENV PATH=/code/.venv/bin:$PATH

WORKDIR /code/apps/sample

# Container Apps routes to port 8080.
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
