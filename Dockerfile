
# Multi-stage build for optimal size and security
FROM python:3.11-slim AS builder

# --- Build arguments for versioning and traceability ---
ARG APP_VERSION=unknown
ARG BUILD_DATE=unknown
ARG VCS_REF=unknown
ARG FLASK_ENV=production

# Make build args available as env vars for scripts if needed
ENV APP_VERSION=${APP_VERSION} \
    BUILD_DATE=${BUILD_DATE} \
    VCS_REF=${VCS_REF} \
    FLASK_ENV=${FLASK_ENV}

WORKDIR /tmp

# Install build dependencies (Playwright, compilers, DB headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Only copy and install dev requirements if FLASK_ENV=development
ARG FLASK_ENV=production
COPY requirements-dev.txt .
RUN if [ "$FLASK_ENV" = "development" ]; then \
    if [ -f requirements-dev.txt ]; then \
        echo "Installing dev requirements..."; \
        pip install --user --no-cache-dir -r requirements-dev.txt; \
    fi; \
fi

# --- Final stage: production image ---
FROM python:3.11-slim

# Repeat ARGs in final stage for label usage
ARG APP_VERSION=unknown
ARG BUILD_DATE=unknown
ARG VCS_REF=unknown
ARG FLASK_ENV=production

# OCI labels for traceability
LABEL org.opencontainers.image.title="Shopping Points Optimiser"
LABEL org.opencontainers.image.description="Maximize cashback and bonus points across programs"
LABEL org.opencontainers.image.created=${BUILD_DATE}
LABEL org.opencontainers.image.revision=${VCS_REF}
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

# Set PATH and PYTHONPATH for installed packages
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

# Health check for container orchestrators
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)" || exit 1

# Use exec form for entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

# ---
# Best practice: Use a .dockerignore file to exclude files/folders not needed in the image (e.g. .git, __pycache__, tests, docs)
