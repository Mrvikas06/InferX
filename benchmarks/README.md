# InferX Benchmark & Load Generation Suite

This folder contains high-throughput synthetic and dataset-driven load generators for stress-testing InferX inference gateway instances.

## Running Load Tests

```bash
# Run 50 requests at concurrency 5
python benchmarks/loadgen.py --num-requests 50 --concurrency 5

# Run streaming SSE benchmarks
python benchmarks/loadgen.py --num-requests 100 --concurrency 10 --stream
```

## Metrics Measured

- **RPS**: Completed requests per second.
- **TPS**: Total token throughput generated across worker pool.
- **Latency**: P50, P95, and P99 response percentiles.
- **TTFT**: Time to First Token under concurrent load.
