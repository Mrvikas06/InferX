#!/usr/bin/env python3
"""InferX Unified Control Plane CLI (inferx_ctl).

Provides operator commands for cluster health, smoke testing,
type checking, testing, and benchmark execution.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


def http_get(url: str, timeout: int = 5) -> Tuple[bool, int, Dict[str, Any]]:
    """Helper to perform HTTP GET returning (ok, status, json_data)."""
    headers = {"User-Agent": "InferX-CTL/1.0", "Accept": "application/json"}
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8")
            data = json.loads(content) if content else {}
            return True, resp.status, data
    except urllib.error.HTTPError as exc:
        return False, exc.code, {}
    except Exception as exc:
        return False, 0, {"error": str(exc)}


def cmd_status(args: argparse.Namespace) -> int:
    """Check health and status of InferX cluster."""
    base_url = args.url.rstrip("/")
    print(f"Connecting to InferX control plane at {base_url}...")
    
    ok, status, health = http_get(f"{base_url}/api/v1/health")
    if not ok:
        print(f"[FAIL] Unable to reach backend at {base_url} (HTTP {status})")
        return 1

    print(f"[OK] Backend Status: {health.get('status', 'healthy')}")
    print(f"     Version       : {health.get('version', '0.1.0')}")

    # Cluster overview
    _, _, cluster = http_get(f"{base_url}/api/v1/cluster/overview")
    if cluster:
        data = cluster.get("data", cluster)
        print(f"     Total Nodes   : {data.get('total_nodes', 'N/A')}")
        print(f"     Deployments   : {data.get('total_deployments', 'N/A')}")
        print(f"     Total Replicas: {data.get('total_replicas', 'N/A')}")
        print(f"     Active Reqs   : {data.get('total_active_requests', 'N/A')}")

    # Telemetry snapshot
    _, _, telem = http_get(f"{base_url}/api/v1/telemetry/overview")
    if telem:
        data = telem.get("data", telem)
        print(f"     Cluster RPS   : {data.get('cluster_rps', 0.0)}")
        print(f"     Cluster P95   : {data.get('cluster_p95_latency_ms', 0.0)} ms")

    return 0


def cmd_models(args: argparse.Namespace) -> int:
    """List registered models exposed via OpenAI-compatible gateway."""
    base_url = args.url.rstrip("/")
    ok, status, payload = http_get(f"{base_url}/v1/models")
    if not ok:
        print(f"[FAIL] Could not query models (HTTP {status})")
        return 1

    models = payload.get("data", [])
    print(f"Models available on {base_url} ({len(models)} total):")
    print("-" * 50)
    for m in models:
        model_id = m.get("id", "unknown")
        created = m.get("created", 0)
        owned_by = m.get("owned_by", "inferx")
        print(f"  * {model_id:<30} owned_by={owned_by} (created={created})")
    print("-" * 50)
    return 0


def cmd_smoke(args: argparse.Namespace) -> int:
    """Run production deployment smoke tests."""
    from scripts.prod_smoke_test import run_smoke_tests
    success = run_smoke_tests(args.url.rstrip("/"), args.frontend.rstrip("/") if args.frontend else "")
    return 0 if success else 1


def cmd_check(args: argparse.Namespace) -> int:
    """Run pyright type check across backend codebase."""
    print("Running Pyright type checking...")
    result = subprocess.run([sys.executable, "-m", "pyright", "backend/app"], capture_output=False)
    return result.returncode


def cmd_test(args: argparse.Namespace) -> int:
    """Run pytest suite."""
    print("Running Pytest suite...")
    import shutil
    pytest_bin = shutil.which("pytest") or sys.executable
    cmd = [pytest_bin, "backend/tests", "-q"] if shutil.which("pytest") else [sys.executable, "-m", "pytest", "backend/tests", "-q"]
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="inferx_ctl",
        description="InferX Production Control Plane CLI",
    )
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="InferX backend URL")
    parser.add_argument("--frontend", default="http://localhost:3000", help="InferX frontend URL")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    subparsers.add_parser("status", help="Query live cluster health and status")
    subparsers.add_parser("models", help="List registered models via OpenAI gateway")
    subparsers.add_parser("smoke", help="Run smoke tests against endpoints")
    subparsers.add_parser("check", help="Run static type analysis with Pyright")
    subparsers.add_parser("test", help="Run full backend test suite")

    args = parser.parse_args()

    commands = {
        "status": cmd_status,
        "models": cmd_models,
        "smoke": cmd_smoke,
        "check": cmd_check,
        "test": cmd_test,
    }

    if not args.command:
        parser.print_help()
        sys.exit(0)

    handler = commands.get(args.command)
    if handler:
        sys.exit(handler(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
