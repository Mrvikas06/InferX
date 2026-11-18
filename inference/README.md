# InferX Inference Engine & Worker Layer

The `inference/` subsystem contains the autonomous serving workers that power model execution within the InferX platform.

## Architecture

InferX separates the **control plane** (request validation, authentication, rate limiting, token quota enforcement, and intelligent routing) from the **inference workers** (model weight execution, KV-cache allocation, continuous batching, and tensor parallelism).

```
                      +-----------------------------+
                      |   InferX Control Plane      |
                      |   (FastAPI Gateway :8000)   |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               |                     |                     |
     (Acquire Replica)       (Acquire Replica)     (Acquire Replica)
               v                     v                     v
      +-----------------+   +-----------------+   +-----------------+
      | Worker Instance |   | Worker Instance |   | Worker Instance |
      | (Worker-01:8001)|   | (Worker-02:8002)|   | (Worker-03:8003)|
      |  Llama-3.3-70B  |   |  Llama-3.3-70B  |   |  Llama-3.3-70B  |
      +-----------------+   +-----------------+   +-----------------+
```

## Running a Worker Locally

You can launch a standalone worker locally with simulated or live vLLM execution:

```bash
# Launch a worker on port 8001
python inference/vllm_worker.py --port 8001 --model meta-llama/Llama-3.3-70B-Instruct

# Launch a secondary worker for cluster scaling tests
python inference/vllm_worker.py --port 8002 --worker-id worker-02 --model meta-llama/Llama-3.3-70B-Instruct
```

## Endpoints Exposed by Each Worker

- `GET /health`: Returns worker status, active request count, KV-cache usage percentage, and GPU load.
- `GET /v1/models`: Returns OpenAI model schema descriptor.
- `POST /v1/chat/completions`: Handles streaming (Server-Sent Events) and non-streaming completions.

## Container Deployment

```bash
cd inference
docker build -t inferx-worker:latest .
docker run -p 8001:8001 inferx-worker:latest
```
