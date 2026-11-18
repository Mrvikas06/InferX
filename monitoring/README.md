# InferX Observability & Monitoring Infrastructure

This directory provides the production-grade Prometheus and Grafana telemetry stack for InferX.

## Stack Components

1. **Prometheus (`:9090`)**: Scrapes real-time OpenMetrics from the InferX backend control plane (`http://backend:8000/metrics`), vLLM inference worker nodes (`:8001`), and NVIDIA DCGM.
2. **Grafana (`:3001`)**: Pre-provisioned dashboards visualizing GPU utilization, VRAM allocation, TTFT, token generation velocity, KV-cache usage, and latency percentiles (P50, P95, P99).
3. **InferX Control Plane (`:8000/metrics`)**: Native exposition endpoint outputting live hardware and inference time-series metrics.

## Quickstart

Start the monitoring stack with Docker Compose:

```bash
docker compose -f monitoring/docker-compose.monitoring.yml up -d
```

### Accessing the UIs:

- **Grafana Dashboard**: [http://localhost:3001](http://localhost:3001)
  - Default Credentials: `admin` / `inferx`
  - Dashboard: *InferX — Cluster & Inference Telemetry*
- **Prometheus Scraper**: [http://localhost:9090](http://localhost:9090)
  - Targets: [http://localhost:9090/targets](http://localhost:9090/targets)
