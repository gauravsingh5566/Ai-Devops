FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY agents/docker-agent/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agents/docker-agent/ .

# Expose port
EXPOSE 8002

# Run API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8002"]
