# InferX System Architecture & Technical Specifications

This document outlines the internal architecture, design principles, and component interactions of the InferX Large Language Model Serving Control Plane.

---

## 1. System Topology

InferX operates as a distributed or single-node control plane managing one or more downstream LLM inference engine processes (such as vLLM, SGLang, or TensorRT-LLM).

```text
[External Clients / SDKs]
          │
          ▼
┌────────────────────────────────────────────────────────┐
│               InferX Gateway (FastAPI)                 │
│                                                        │
│  ┌───────────────────┐        ┌─────────────────────┐  │
│  │ Security Headers  │        │ Rate Limiter & RBAC │  │
│  └─────────┬─────────┘        └──────────┬──────────┘  │
│            ▼                             ▼             │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Token Quota Accounting Ledger          │  │
│  └─────────────────────────┬────────────────────────┘  │
│                            ▼                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │             Cluster Load Balancer                │  │
│  │     (Least Connections / Weighted Latency / RR)   │  │
│  └──────────┬───────────────────────────┬───────────┘  │
└─────────────┼───────────────────────────┼──────────────┘
              ▼                           ▼
    ┌───────────────────┐       ┌───────────────────┐
    │  vLLM Worker 1    │       │  vLLM Worker 2    │
    │  (Port 8000)      │       │  (Port 8001)      │
    └───────────────────┘       └───────────────────┘
```

---

## 2. Core Architectural Subsystems

### 2.1 Inference Gateway (`backend/app/services/inference_gateway.py`)
- **OpenAI Compatibility**: Mounts standard `/v1/chat/completions` and `/v1/models` endpoints.
- **Dual Execution Modes**:
  - **Streaming**: Uses `httpx.AsyncClient.stream` to forward token chunks as Server-Sent Events (`text/event-stream`), emitting SSE chunks compliant with OpenAI standards.
  - **Non-Streaming**: Forwards atomic completion payloads, capturing round-trip latency, Time-To-First-Token (TTFT), and token generation rates ($tok/sec$).
- **Software Simulation Fallback**: When downstream sockets are not yet provisioned, the gateway safely emits mock responses with authentic latency simulation, ensuring test harness reliability without requiring high-end physical GPUs.

### 2.2 Intelligent Load Balancer (`backend/app/services/load_balancer.py`)
- **Replica Instance Tracking**: Each worker replica maintains:
  - `active_requests`: Atomic inflight request counter.
  - `avg_latency_ms`: Exponential Moving Average (EMA, $\alpha = 0.2$) of response durations.
  - `error_count`: Consecutive network failure count.
  - `status`: `healthy`, `unhealthy`, `starting`, `draining`, `stopped`.
- **Supported Strategies**:
  - `least_connections` (default): Routes traffic to the replica with the minimum active inflight requests, using lowest average latency as tie-breaker.
  - `round_robin`: Cyclic distribution across healthy workers.
  - `weighted_latency`: Routes to workers with the lowest historical EMA latency.
- **Self-Healing & Health Degradation**: 3 consecutive connection timeouts or 5xx responses automatically transitions an instance to `unhealthy`. A single successful probe restores the instance to `healthy`.

### 2.3 Autoscaling Policy Engine (`backend/app/services/autoscaler.py`)
- **Metrics Evaluated**:
  - `qps`: Queries per second per worker.
  - `latency_ms`: P95 round-trip latency.
  - `queue_depth`: Total inflight requests across all replicas.
  - `gpu_util`: Physical GPU utilization percentage via NVML.
- **Damping & Anti-Flapping**: Implements separate `scale_up_cooldown` (default 60s) and `scale_down_cooldown` (default 180s) windows to prevent thrashing under oscillating load spikes.
- **Clamping**: Desired replicas are bounded strictly by $[min\_replicas, max\_replicas]$.

### 2.4 GPU Hardware Telemetry (`backend/app/services/gpu_monitor.py`)
- **NVIDIA Management Library (NVML)**: Direct C-bindings through `pynvml` query:
  - Core GPU utilization (%)
  - VRAM memory allocated vs total (MB)
  - Core temperature (°C)
  - Board power draw (Watts)
  - Graphics clock frequency (MHz)
- **Host Resources**: Tracks host CPU load, total/used RAM, and disk storage through `psutil`.

### 2.5 Automated Benchmarking Suite (`backend/app/services/benchmark_runner.py`)
- **Asynchronous Worker Pool**: Dispatches synthetic prompts using an `asyncio.Semaphore` pool up to the requested concurrency limit (e.g. 16, 32, 64).
- **Statistical Metric Calculation**: Calculates $P_{50}, P_{95}, P_{99}$ latency percentiles, Time-To-First-Token (TTFT), and Time-Per-Output-Token (TPOT / ITL).
- **Histogram Quantization**: Produces latency distribution bins for visual chart rendering.

### 2.6 Enterprise Governance & Token Quotas (`backend/app/repositories/quota_repository.py`)
- **Quota Budgets**: Configurable token caps per user, API key, or tenant organization.
- **Auto-Rollover**: Automatically resets daily token counters when UTC date increments, and monthly counters on month boundaries.
- **Pre-Flight Gating**: Rejects requests with HTTP 429 when daily or monthly token budgets are depleted.
- **Compliance Export**: Streams audit events in RFC 4180 CSV or JSON format for SOC2 and security audits.

---

## 3. Database Schema

The relational database layer (PostgreSQL in production, SQLite in development) contains:
- `users`: Accounts, password hashes, and RBAC roles (`admin`, `operator`, `viewer`).
- `api_keys`: Hashed keys (`ifx_live_...`), prefix identifiers, and rate limit rules.
- `models`: Hugging Face repo metadata, context length, parameters, and cache paths.
- `deployments`: Serving instances, tensor parallelism, ports, and replica targets.
- `scaling_policies`: Min/max replicas, target metrics, and cooldown timers.
- `quota_policies`: Token budget caps, live usage counters, and rate limits.
- `benchmarks`: Concurrency sweeps, throughput metrics, and latency percentiles.
- `audit_logs`: Immutable security audit trails.
