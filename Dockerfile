# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/devcontainers/universal:2

WORKDIR /workspace

# Copy repository files
COPY . .

# Install Python and Node dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir pytest psutil \
    && npm ci

CMD ["bash"]
