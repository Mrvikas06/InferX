"""OpenAI-Compatible Inference Gateway Endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import AuthContext, get_current_auth, get_optional_auth_context
from backend.app.core.rate_limit import check_rate_limit
from backend.app.db.session import get_db
from backend.app.schemas.inference import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    OpenAIEngineModelCard,
    OpenAIModelListResponse,
)
from backend.app.services.inference_gateway import (
    forward_chat_completion,
    get_active_openai_models,
    resolve_target_deployment,
    stream_chat_completion,
)

logger = logging.getLogger("inferx.api.inference")

router = APIRouter()


@router.post(
    "/chat/completions",
    response_model=ChatCompletionResponse,
    summary="Create chat completion",
    description="OpenAI-compatible chat completion endpoint supporting streaming SSE and non-streaming forwarding to active vLLM deployments.",
)
async def create_chat_completion(
    request: Request,
    body: ChatCompletionRequest,
    response: Response,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
):
    """Process OpenAI-standard chat completion request."""
    # 1. Enforce rate limiting per authenticated actor
    allowed, remaining, reset_secs = await check_rate_limit(
        identifier=f"actor:{auth.actor_id}",
        max_requests=100,
        window_seconds=60,
    )
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(reset_secs)},
            content={
                "error": {
                    "message": "Rate limit exceeded. Too many inference requests.",
                    "type": "rate_limit_error",
                    "code": 429,
                }
            },
        )

    # 2. Resolve target running deployment for the requested model
    deployment, error_reason = await resolve_target_deployment(db, body.model)

    if error_reason == "not_found":
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "message": f"Model '{body.model}' is not registered or has no deployment.",
                    "type": "invalid_request_error",
                    "param": "model",
                    "code": "model_not_found",
                }
            },
        )
    elif error_reason == "starting":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={"Retry-After": "5"},
            content={
                "error": {
                    "message": f"Deployment for '{body.model}' is initializing. Retry in a few seconds.",
                    "type": "service_unavailable",
                    "param": "model",
                    "code": 503,
                }
            },
        )
    elif error_reason == "stopped":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "message": f"Deployment for model '{body.model}' is stopped. Please start it.",
                    "type": "invalid_request_error",
                    "param": "model",
                    "code": "model_stopped",
                }
            },
        )

    assert deployment is not None

    # 3. Handle Streaming Response (Server-Sent Events)
    if body.stream:
        return StreamingResponse(
            stream_chat_completion(deployment, body),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-InferX-Deployment-Id": deployment.id,
                "X-InferX-Deployment-Port": str(deployment.port),
            },
        )

    # 4. Handle Non-Streaming Response
    result, metrics = await forward_chat_completion(deployment, body)

    # Inject performance telemetry into response headers
    if "latency_ms" in metrics:
        response.headers["X-InferX-Latency-Ms"] = str(metrics["latency_ms"])
    if "ttft_ms" in metrics:
        response.headers["X-InferX-TTFT-Ms"] = str(metrics["ttft_ms"])
    if "tokens_per_sec" in metrics:
        response.headers["X-InferX-Tokens-Per-Sec"] = str(metrics["tokens_per_sec"])
    response.headers["X-InferX-Deployment-Id"] = deployment.id

    return result


@router.get(
    "/models",
    response_model=OpenAIModelListResponse,
    summary="List available OpenAI models",
    description="Returns list of models currently served by active deployments.",
)
async def list_openai_models(
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
):
    """List all serving models available for OpenAI inference requests."""
    models = await get_active_openai_models(db)
    return OpenAIModelListResponse(data=models)


@router.get(
    "/models/{model_id:path}",
    response_model=OpenAIEngineModelCard,
    summary="Retrieve model info",
)
async def get_openai_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    auth: Optional[AuthContext] = Depends(get_optional_auth_context),
):
    """Retrieve details for a specific model ID."""
    models = await get_active_openai_models(db)
    for m in models:
        if m.id == model_id:
            return m

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": {
                "message": f"Model '{model_id}' does not exist or is not actively serving.",
                "type": "invalid_request_error",
                "code": "model_not_found",
            }
        },
    )
