# Notifier Service Dockerfile - Multi-stage build
# FastAPI service for sending email notifications

# ===========================
# Stage 1: Builder
# ===========================
FROM python:3.11-alpine AS builder

# Install build dependencies (Alpine packages)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    # Remove unnecessary build tools from venv to reduce size
    pip uninstall -y pip setuptools && \
    # Remove .pyc files and caches
    find /opt/venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name '*.pyc' -delete && \
    find /opt/venv -type f -name '*.pyo' -delete

# ===========================
# Stage 2: Runtime
# ===========================
FROM python:3.11-alpine

LABEL maintainer="DevOps Team"
LABEL description="Email notifier service for DevOps RCA Agent"
LABEL version="0.1.0"

# Install runtime dependencies only
RUN apk add --no-cache \
    libstdc++ \
    libgcc \
    && rm -rf /var/cache/apk/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment to use virtual environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy application code and templates
COPY main.py .
COPY templates/ ./templates/

# Create non-root user for security
RUN addgroup -g 1000 notifier && \
    adduser -D -u 1000 -G notifier notifier && \
    chown -R notifier:notifier /app

# Switch to non-root user
USER notifier

# Expose port
EXPOSE 8080

# Health check using Python built-in (no extra dependencies)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health', timeout=2)" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
