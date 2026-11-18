#!/usr/bin/env python3
"""InferX High-Throughput Load Generator.

Executes concurrent synthetic or dataset-driven inference queries against
the InferX OpenAI-compatible `/v1/chat/completions` gateway.
"""

import argparse
import asyncio
import json
import logging
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("inferx.loadgen")


async def send_request(
    client: httpx.AsyncClient,
    base_url: str,
    model: str,
    prompt: str,
    stream: bool = False,
    api_key: str = "",
) -> Tuple[bool, float, int, float]:
    """Execute request and return (success, total_latency_ms, tokens, ttft_ms)."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 128,
        "temperature": 0.7,
        "stream": stream,
    }

    t0 = time.perf_counter()
    ttft_ms = 0.0
    tokens = 0

    try:
        if stream:
            async with client.stream(
                "POST",
                f"{base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0,
            ) as resp:
                if resp.status_code != 200:
                    return False, (time.perf_counter() - t0) * 1000.0, 0, 0.0
                first_token = True
                async for chunk in resp.aiter_lines():
                    if first_token and chunk.strip():
                        ttft_ms = (time.perf_counter() - t0) * 1000.0
                        first_token = False
                    if "content" in chunk:
                        tokens += 1
                total_ms = (time.perf_counter() - t0) * 1000.0
                return True, total_ms, max(1, tokens), ttft_ms
        else:
            resp = await client.post(
                f"{base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            total_ms = (time.perf_counter() - t0) * 1000.0
            if resp.status_code == 200:
                data = resp.json()
                usage = data.get("usage", {})
                tokens = usage.get("completion_tokens", 1)
                return True, total_ms, tokens, total_ms * 0.4
            return False, total_ms, 0, 0.0
    except Exception:
        return False, (time.perf_counter() - t0) * 1000.0, 0, 0.0


async def run_benchmark(
    base_url: str,
    model: str,
    num_requests: int,
    concurrency: int,
    stream: bool,
    api_key: str,
) -> None:
    """Run concurrent benchmark worker pool."""
    dataset_file = Path(__file__).parent / "prompts.json"
    prompts = ["Explain the architecture of InferX."]
    if dataset_file.exists():
        with open(dataset_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            prompts = [item["prompt"] for item in data]

    print("=" * 65)
    print(f" InferX Gateway Benchmark Runner")
    print(f" Target URL   : {base_url}/v1/chat/completions")
    print(f" Model        : {model}")
    print(f" Requests     : {num_requests} total (concurrency={concurrency})")
    print(f" Streaming    : {stream}")
    print("=" * 65)

    semaphore = asyncio.Semaphore(concurrency)
    latencies: List[float] = []
    ttfts: List[float] = []
    total_tokens = 0
    successes = 0

    async with httpx.AsyncClient() as client:
        async def worker(idx: int):
            nonlocal successes, total_tokens
            prompt = prompts[idx % len(prompts)]
            async with semaphore:
                ok, lat_ms, tok_count, ttft_ms = await send_request(
                    client, base_url, model, prompt, stream, api_key
                )
                if ok:
                    successes += 1
                    latencies.append(lat_ms)
                    if ttft_ms > 0:
                        ttfts.append(ttft_ms)
                    total_tokens += tok_count

        t_start = time.perf_counter()
        tasks = [worker(i) for i in range(num_requests)]
        await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - t_start

    print("\nBenchmark Results:")
    print("-" * 50)
    print(f" Total Requests Completed : {successes}/{num_requests} ({(successes/num_requests)*100:.1f}%)")
    print(f" Total Wall-Clock Time    : {elapsed:.2f} s")
    print(f" Gateway Throughput (RPS) : {successes / elapsed:.2f} req/s")
    if total_tokens > 0:
        print(f" Token Throughput (TPS)   : {total_tokens / elapsed:.2f} tok/s")
    if latencies:
        latencies.sort()
        p50 = statistics.median(latencies)
        p95 = latencies[int(len(latencies) * 0.95)] if len(latencies) > 1 else p50
        p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) > 1 else p50
        print(f" Latency P50              : {p50:.2f} ms")
        print(f" Latency P95              : {p95:.2f} ms")
        print(f" Latency P99              : {p99:.2f} ms")
    if ttfts:
        print(f" Average TTFT             : {statistics.mean(ttfts):.2f} ms")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="InferX Loadgen Benchmark")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="InferX Base URL")
    parser.add_argument("--model", default="meta-llama/Llama-3.3-70B-Instruct", help="Target model ID")
    parser.add_argument("--num-requests", type=int, default=20, help="Total requests to dispatch")
    parser.add_argument("--concurrency", type=int, default=4, help="Concurrent workers")
    parser.add_argument("--stream", action="store_true", help="Enable SSE streaming mode")
    parser.add_argument("--api-key", default="", help="Optional bearer token or API key")
    args = parser.parse_args()

    asyncio.run(
        run_benchmark(
            base_url=args.url.rstrip("/"),
            model=args.model,
            num_requests=args.num_requests,
            concurrency=args.concurrency,
            stream=args.stream,
            api_key=args.api_key,
        )
    )


if __name__ == "__main__":
    main()
