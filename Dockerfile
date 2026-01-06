# Multi-stage build für optimale Größe
FROM python:3.11-slim as builder

# Build arguments
ARG APP_VERSION=unknown
ARG BUILD_DATE=unknown
ARG VCS_REF=unknown

WORKDIR /tmp

# Dependencies für Playwright und andere tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements und install
COPY requirements.txt .
COPY requirements-dev.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Install dev requirements if FLASK_ENV is development
ARG FLASK_ENV=production
RUN if [ "$FLASK_ENV" = "development" ]; then \
    pip install --user --no-cache-dir -r requirements-dev.txt; \
    fi

# Final stage - Production image
FROM python:3.11-slim

# Image metadata (OCI labels)
ARG APP_VERSION=unknown
ARG BUILD_DATE=unknown
ARG VCS_REF=unknown

LABEL org.opencontainers.image.title="Shopping Points Optimiser"
LABEL org.opencontainers.image.description="Maximize cashback and bonus points across programs"
LABEL org.opencontainers.image.version="${APP_VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.vendor="Shopping Points Optimiser Team"
LABEL org.opencontainers.image.source="https://github.com/kduchrow/shopping_points_optimiser"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*



# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Set PATH and PYTHONPATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH

# Install Playwright browser binaries and system deps (Chromium)
RUN python -m playwright install-deps chromium && \
    python -m playwright install chromium

# Copy application code
COPY . .

# Copy and set permissions for entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)" || exit 1

# Use entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]
