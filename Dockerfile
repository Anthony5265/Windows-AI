FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install only the native libraries required to build/runtime dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies before copying application source for better layer reuse.
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the canonical application components.
COPY windows_ai/ ./windows_ai/
COPY marketplace/ ./marketplace/
COPY config/ ./config/

# Run the service as an unprivileged user.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000 8001 5000

# Use Python's standard library for the health check so it does not depend on
# an optional third-party HTTP client being installed.
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read()" || exit 1

CMD ["python", "-m", "windows_ai"]
