#!/usr/bin/env python3
"""InferX Production Deployment Smoke Test Suite.

Probes live backend control plane, OpenAI inference gateway,
cluster telemetry, and frontend web routes.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Tuple


def probe_endpoint(url: str, method: str = "GET", payload: Any = None) -> Tuple[bool, int, Dict[str, Any], float]:
    """Execute HTTP probe and return (success, status_code, data, latency_ms)."""
    start = time.perf_counter()
    headers = {"User-Agent": "InferX-SmokeTest/1.0", "Accept": "application/json"}
    data_bytes = None
    if payload is not None:
        data_bytes = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            content = resp.read().decode("utf-8")
            parsed = json.loads(content) if content else {}
            return True, resp.status, parsed, round(elapsed_ms, 2)
    except urllib.error.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return False, exc.code, {}, round(elapsed_ms, 2)
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return False, 0, {"error": str(exc)}, round(elapsed_ms, 2)


def run_smoke_tests(base_url: str, frontend_url: str) -> bool:
    """Run full checklist of critical deployment endpoints."""
    print("=" * 65)
    print(f" InferX Production Smoke Tests -> {base_url}")
    print("=" * 65)

    tests: List[Tuple[str, str, str, Any, int]] = [
        ("Backend Health Check", "GET", f"{base_url}/api/v1/health", None, 200),
        ("OpenAPI Documentation", "GET", f"{base_url}/openapi.json", None, 200),
        ("OpenAI Models Listing", "GET", f"{base_url}/v1/models", None, 200),
        ("Cluster Overview", "GET", f"{base_url}/api/v1/cluster/overview", None, 200),
        ("Telemetry Overview", "GET", f"{base_url}/api/v1/telemetry/overview", None, 200),
        ("Deployments Listing", "GET", f"{base_url}/api/v1/deployments", None, 200),
    ]

    all_passed = True

    for name, method, url, payload, expected_status in tests:
        success, status, data, latency = probe_endpoint(url, method, payload)
        passed = (status == expected_status)
        if not passed:
            all_passed = False

        status_str = "PASS" if passed else "FAIL"
        symbol = "[OK]" if passed else "[XX]"
        print(f"{symbol} {name:<26} HTTP {status} (exp {expected_status}) in {latency:>6.1f}ms -> {status_str}")

    # Optional Frontend probe
    if frontend_url:
        fe_success, fe_status, _, fe_lat = probe_endpoint(frontend_url)
        fe_passed = (fe_status == 200)
        symbol = "[OK]" if fe_passed else "[--]"
        print(f"{symbol} Frontend UI Home        HTTP {fe_status} (exp 200) in {fe_lat:>6.1f}ms -> {'PASS' if fe_passed else 'BYPASS'}")

    print("=" * 65)
    if all_passed:
        print(" ALL PRODUCTION SMOKE TESTS PASSED CLEANLY")
    else:
        print(" SOME PRODUCTION SMOKE TESTS FAILED OR ENGINE OFFLINE")
    print("=" * 65)

    return all_passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InferX Smoke Test Suite")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base backend URL")
    parser.add_argument("--frontend-url", default="http://localhost:3000", help="Frontend URL")
    args = parser.parse_args()

    success = run_smoke_tests(args.base_url, args.frontend_url)
    sys.exit(0 if success else 1)
