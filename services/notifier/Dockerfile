# Notifier Service Dockerfile
# FastAPI service for sending email notifications

FROM python:3.11-slim

LABEL maintainer="DevOps Team"
LABEL description="Email notifier service for DevOps RCA Agent"

# Set working directory
WORKDIR /app

# Install dependencies first (for better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create non-root user for security
RUN useradd -m -u 1000 notifier && \
    chown -R notifier:notifier /app

# Switch to non-root user
USER notifier

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
