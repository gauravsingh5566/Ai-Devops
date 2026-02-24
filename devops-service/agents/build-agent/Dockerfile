FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*
COPY agents/build-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agents/build-agent/ .
EXPOSE 8001
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]