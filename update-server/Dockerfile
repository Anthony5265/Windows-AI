FROM python:3.11-slim

LABEL maintainer="Windows AI Team"
LABEL description="Windows AI Update Server"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY windows_ai/ windows_ai/
COPY update-server/ update-server/

# Create downloads directory
RUN mkdir -p update-server/downloads

# Expose port
EXPOSE 8011

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8011/health || exit 1

# Run server
CMD ["python", "update-server/server.py", "--host", "0.0.0.0", "--port", "8011"]
