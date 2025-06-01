# Dependency-only build for DevOps AI Agent
FROM python:3.13-slim as dependencies

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src" \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app user and add to root group for Docker socket access
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && usermod -a -G root appuser

# Set working directory
WORKDIR /app

# Copy and install Python dependencies ONLY
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create source directory structure (will be mounted as volume)
RUN mkdir -p /app/src && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Runtime stage - no source code copying
FROM dependencies as runtime

# Set user
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application (source code mounted as volume)
CMD ["python", "-m", "uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8001"]