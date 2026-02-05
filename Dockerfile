# AI Red Blue Platform - Production Dockerfile
FROM python:3.12-slim

LABEL maintainer="AI Red Blue Team"
LABEL description="AI+ Red and Blue Security Platform"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-interaction --no-ansi

# Copy application code
COPY apps/ ./apps/
COPY libs/ ./libs/
COPY packages/ ./packages/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the dashboard by default
CMD ["poetry", "run", "python", "apps/dashboard/main.py"]
