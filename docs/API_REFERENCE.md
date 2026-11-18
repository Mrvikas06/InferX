# InferX API Reference & Developer Guide

Complete API documentation for the InferX Control Plane and Inference Gateway.

All endpoints support standard JSON request/response formats. Authentication can be provided via JWT Bearer tokens or InferX API keys (`X-API-Key: ifx_live_...`).

---

## 1. OpenAI-Compatible Inference Gateway

### Create Chat Completion
`POST /v1/chat/completions` or `POST /api/v1/chat/completions`

Creates a model completion for the provided chat messages. Supports both Server-Sent Events (SSE) streaming and atomic responses.

**Request Headers:**
```http
Content-Type: application/json
Authorization: Bearer <token>
# OR: X-API-Key: <api_key>
```

**Request Body:**
```json
{
  "model": "meta-llama/Llama-3.3-70B-Instruct",
  "messages": [
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "Write a Python function to compute fibonacci numbers."}
  ],
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": false
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_jwt_or_key>" \
  -d '{
    "model": "meta-llama/Llama-3.3-70B-Instruct",
    "messages": [{"role": "user", "content": "Hello InferX!"}],
    "temperature": 0.5
  }'
```

**Response Headers:**
- `X-InferX-Deployment-Id`: UUID of the serving deployment
- `X-InferX-Deployment-Port`: Host port of the serving replica
- `X-InferX-Latency-Ms`: Total response generation latency
- `X-InferX-TTFT-Ms`: Time to first token
- `X-InferX-Tokens-Per-Sec`: Generated tokens per second
- `X-InferX-Quota-Remaining`: Remaining daily token budget

---

## 2. Cluster Scaling & Load Balancing

### Get Cluster Overview
`GET /api/v1/cluster/overview`

Returns aggregate cluster capacity, total replicas, active requests, and routing strategy.

**cURL Example:**
```bash
curl http://localhost:8000/api/v1/cluster/overview \
  -H "Authorization: Bearer <token>"
```

### Manually Scale Deployment Replicas
`POST /api/v1/cluster/deployments/{id}/scale`

Dynamically allocates or drains worker replica instances.

**Request Body:**
```json
{
  "replicas": 4
}
```

### Inspect Worker Replicas
`GET /api/v1/cluster/deployments/{id}/replicas`

Returns live status, port allocation, active inflight requests, total processed requests, and moving average latency for each worker.

---

## 3. Automated Benchmarking Suite

### Launch Benchmark Run
`POST /api/v1/benchmarks`

Triggers an asynchronous multi-concurrency load test against a deployment.

**Request Body:**
```json
{
  "name": "Llama 70B Stress Sweep",
  "deployment_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "concurrency": 16,
  "num_prompts": 64,
  "input_tokens": 256,
  "output_tokens": 128
}
```

### Fetch Benchmark Report
`GET /api/v1/benchmarks/{id}`

Returns throughput ($RPS$, $tok/sec$), latency percentiles ($P_{50}, P_{95}, P_{99}$), TTFT, and latency histogram bins.

---

## 4. Hardware Telemetry & Monitoring

### Get System & GPU Overview
`GET /api/v1/telemetry/overview`

Returns live NVIDIA NVML metrics (VRAM usage, GPU clock, temperature, board power), host resources, and rolling latency buffers.

### Get 60-Point Time Series History
`GET /api/v1/telemetry/history`

Returns historical 10-second data points formatted for frontend charting.

---

## 5. Enterprise Governance & Token Quotas

### Define Quota Policy
`POST /api/v1/governance/quotas`

**Request Body:**
```json
{
  "name": "Engineering Team Tier",
  "target_type": "tenant",
  "target_id": "org-engineering",
  "max_tokens_per_day": 5000000,
  "max_tokens_per_month": 100000000,
  "rate_limit_rpm": 600,
  "is_active": true
}
```

### Inspect Quota Usage & Balance
`GET /api/v1/governance/quotas/{id}/usage`

### Export Compliance Audit Logs
`GET /api/v1/audit-logs/export?format=csv` (or `?format=json`)

Downloads compliance audit trails in streaming RFC 4180 CSV or JSON format.
