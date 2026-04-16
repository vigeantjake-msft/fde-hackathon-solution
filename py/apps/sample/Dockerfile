ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /bin/

WORKDIR /code

# Copy workspace-level files needed for uv workspace resolution
COPY pyproject.toml uv.lock ./

# Copy the sample app
COPY apps/sample/ ./apps/sample/

# Copy the shared common libraries (namespace packages used by models.py)
COPY common/ ./common/

# Install dependencies into the workspace virtualenv
RUN uv sync --package sample --frozen --no-cache

# Set PYTHONPATH so the app can import from the common libs src directories
ENV PYTHONPATH=/code/apps/sample:/code/common/libs/models/src:/code/common/libs/fastapi/src:/code/common/libs/fdebenchkit/src

WORKDIR /code/apps/sample

# Container Apps routes to port 8080
EXPOSE 8080

CMD ["uv", "run", "--package", "sample", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
