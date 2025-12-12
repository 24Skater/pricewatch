# =============================================================================
# Pricewatch Docker Image
# =============================================================================
# Multi-stage build for optimized production image
# =============================================================================

# -----------------------------------------------------------------------------
# Build Stage
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Production Stage
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS production

# Labels for image metadata
LABEL org.opencontainers.image.title="Pricewatch"
LABEL org.opencontainers.image.description="Enterprise price tracking application"
LABEL org.opencontainers.image.version="2.1.0"
LABEL org.opencontainers.image.vendor="Pricewatch"
LABEL org.opencontainers.image.source="https://github.com/pricewatch/pricewatch"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appgroup . .

# Remove unnecessary files
RUN rm -rf tests/ .git/ .gitignore .env* *.md docs/ .coverage htmlcov/ .pytest_cache/

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appgroup /app/logs /app/data

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
