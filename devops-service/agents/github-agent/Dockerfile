FROM python:3.11-slim

WORKDIR /app

# Install git (required for cloning)
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY agents/github-agent/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared /app/shared

# Copy application code
COPY agents/github-agent/ .

# Create workspace directory
RUN mkdir -p /workspace

# Expose port
EXPOSE 8007

# Run API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8007"]