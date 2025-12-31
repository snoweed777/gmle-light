# GMLE Light Dockerfile
# Lightweight MCQ Generator with Local Anki Integration
#
# Features:
# - Python 3.11 + FastAPI REST API
# - React + Vite GUI
# - No Anki/Xvfb/X11 (Anki runs on host Mac)

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install frontend dependencies
COPY frontend/package*.json frontend/
RUN cd frontend && npm ci

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x docker-entrypoint.sh && \
    chmod +x scripts/service/*.sh 2>/dev/null || true && \
    chmod +x scripts/lib/*.sh 2>/dev/null || true

# Expose ports (API + GUI only, Anki is on host)
EXPOSE 8000 3001

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command
CMD ["/bin/bash"]

