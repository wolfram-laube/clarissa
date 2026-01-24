# CLARISSA API Service
# Multi-stage build for production-ready image

# ============== Builder Stage ==============
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============== Runtime Stage ==============
FROM python:3.12-slim as runtime

WORKDIR /app

# Install runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash clarissa

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=clarissa:clarissa src/ /app/src/

# Switch to non-root user
USER clarissa

# Environment
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn
CMD ["python", "-m", "uvicorn", "clarissa.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
