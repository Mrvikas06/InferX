"""vLLM Inference Engine Process Runner and Simulation Adapter."""

import asyncio
from datetime import datetime, timezone
import json
import logging
import os
import shutil
import sys
import time
from typing import Any, Dict, Optional, Tuple
import uuid

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from backend.app.schemas.inference import (
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionChoice,
    CompletionUsage,
    ChatMessage,
)

logger = logging.getLogger("inferx.vllm_runner")

# Tracking active runner state per deployment:
# deployment_id -> {"type": "subprocess" | "mock_server", "process": ..., "server": ..., "task": ...}
_ACTIVE_ENGINES: Dict[str, Dict[str, Any]] = {}


def is_vllm_available() -> bool:
    """Detect whether genuine vLLM package or binary is installed in python environment."""
    return shutil.which("vllm") is not None or "vllm" in sys.modules


def create_mock_engine_app(model_name: str) -> FastAPI:
    """Create a lightweight ASGI app simulating OpenAI API server for testing & GPU-less environments."""
    app = FastAPI(title=f"InferX Mock vLLM Engine - {model_name}")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "engine": "mock-vllm", "model": model_name}

    @app.get("/v1/models")
    async def list_models():
        return {
            "object": "list",
            "data": [
                {
                    "id": model_name,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "inferx-mock",
                    "permission": [],
                    "root": model_name,
                    "parent": None,
                }
            ],
        }

    @app.post("/v1/chat/completions")
    async def chat_completions(req: ChatCompletionRequest):
        req_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())
        last_user_msg = next((m.content for m in reversed(req.messages) if m.role == "user"), "Hello!")
        simulated_text = (
            f"[InferX Engine serving {model_name}]\n"
            f"Processed your prompt: '{last_user_msg[:60]}...'\n"
            f"Deployment parameters applied: temp={req.temperature}, top_p={req.top_p}."
        )

        prompt_tokens = sum(len(m.content.split()) for m in req.messages) + 8
        completion_tokens = len(simulated_text.split())

        if not req.stream:
            return ChatCompletionResponse(
                id=req_id,
                created=created,
                model=model_name,
                choices=[
                    CompletionChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content=simulated_text),
                        finish_reason="stop",
                    )
                ],
                usage=CompletionUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                ),
            )

        # Streaming SSE generation
        async def event_generator():
            words = simulated_text.split(" ")
            # Initial role delta
            first_chunk = ChatCompletionChunk(
                id=req_id,
                created=created,
                model=model_name,
                choices=[
                    ChatCompletionChunkChoice(
                        index=0,
                        delta=ChatCompletionChunkDelta(role="assistant", content=""),
                        finish_reason=None,
                    )
                ],
            )
            yield f"data: {first_chunk.model_dump_json()}\n\n"
            await asyncio.sleep(0.03)

            for i, word in enumerate(words):
                chunk = ChatCompletionChunk(
                    id=req_id,
                    created=created,
                    model=model_name,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=0,
                            delta=ChatCompletionChunkDelta(content=word + (" " if i < len(words) - 1 else "")),
                            finish_reason=None,
                        )
                    ],
                )
                yield f"data: {chunk.model_dump_json()}\n\n"
                await asyncio.sleep(0.02)  # Simulate token generation pacing

            final_chunk = ChatCompletionChunk(
                id=req_id,
                created=created,
                model=model_name,
                choices=[
                    ChatCompletionChunkChoice(
                        index=0,
                        delta=ChatCompletionChunkDelta(),
                        finish_reason="stop",
                    )
                ],
            )
            yield f"data: {final_chunk.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return app


async def start_engine(
    deployment_id: str,
    model_name: str,
    port: int,
    host: str = "127.0.0.1",
    engine: str = "vllm",
    tensor_parallel: int = 1,
    max_model_len: int = 4096,
    gpu_memory_utilization: float = 0.90,
    force_mock: bool = False,
) -> bool:
    """
    Launch inference engine worker. If genuine vLLM is not installed or force_mock is True,
    runs an in-process mock server bound to the allocated TCP port.
    """
    # Stop existing instance if running
    if deployment_id in _ACTIVE_ENGINES:
        await stop_engine(deployment_id)

    use_genuine_vllm = is_vllm_available() and not force_mock and os.getenv("INFERX_FORCE_MOCK_ENGINE") != "true"

    if use_genuine_vllm:
        cmd = [
            sys.executable,
            "-m",
            "vllm.entrypoints.openai.api_server",
            "--model",
            model_name,
            "--host",
            host,
            "--port",
            str(port),
            "--tensor-parallel-size",
            str(tensor_parallel),
            "--max-model-len",
            str(max_model_len),
            "--gpu-memory-utilization",
            str(gpu_memory_utilization),
        ]
        logger.info("Spawning genuine vLLM process for %s on %s:%d", deployment_id, host, port)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _ACTIVE_ENGINES[deployment_id] = {
                "type": "subprocess",
                "process": proc,
                "port": port,
                "host": host,
            }
            return True
        except Exception as exc:
            logger.error("Failed to spawn vLLM subprocess: %s", exc)
            return False
    else:
        # Launch lightweight mock server on the designated TCP port
        logger.info("Spawning simulated inference engine for %s on %s:%d", deployment_id, host, port)
        mock_app = create_mock_engine_app(model_name)
        config = uvicorn.Config(
            app=mock_app,
            host=host,
            port=port,
            log_level="warning",
            loop="asyncio",
        )
        server = uvicorn.Server(config)
        task = asyncio.create_task(server.serve())

        _ACTIVE_ENGINES[deployment_id] = {
            "type": "mock_server",
            "server": server,
            "task": task,
            "port": port,
            "host": host,
        }

        # Give server a moment to bind socket
        for _ in range(20):
            if server.started:
                break
            await asyncio.sleep(0.05)

        return True


async def stop_engine(deployment_id: str) -> bool:
    """Gracefully terminate engine worker and free TCP socket."""
    info = _ACTIVE_ENGINES.pop(deployment_id, None)
    if not info:
        return False

    if info["type"] == "subprocess":
        proc = info["process"]
        try:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=4.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
            return True
        except Exception as exc:
            logger.warning("Error terminating subprocess for %s: %s", deployment_id, exc)
            return False

    elif info["type"] == "mock_server":
        server = info["server"]
        task = info["task"]
        server.should_exit = True
        try:
            await asyncio.wait_for(task, timeout=3.0)
        except Exception:
            task.cancel()
        return True

    return False


def is_engine_active(deployment_id: str) -> bool:
    """Check if worker process or server is actively running."""
    info = _ACTIVE_ENGINES.get(deployment_id)
    if not info:
        return False
    if info["type"] == "subprocess":
        return info["process"].returncode is None
    if info["type"] == "mock_server":
        return info["server"].started and not info["server"].should_exit
    return False
