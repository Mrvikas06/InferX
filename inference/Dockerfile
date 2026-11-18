# InferX Inference Worker Dockerfile
FROM python:3.12-slim AS worker-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vllm_worker.py config.yaml ./

EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

ENTRYPOINT ["python", "vllm_worker.py"]
CMD ["--host", "0.0.0.0", "--port", "8001", "--model", "meta-llama/Llama-3.3-70B-Instruct"]
