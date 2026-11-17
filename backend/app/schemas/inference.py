"""OpenAI-Compatible Inference Request and Response Schemas."""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single message within a chat completion prompt sequence."""

    role: Literal["system", "user", "assistant", "tool"] = Field(
        ..., description="The role of the author of this message."
    )
    content: str = Field(..., description="The contents of the message.")
    name: Optional[str] = Field(default=None, description="Optional name of the participant.")


class ChatCompletionRequest(BaseModel):
    """OpenAI-compliant chat completion request schema."""

    model: str = Field(..., description="ID of the model or running deployment to use.")
    messages: List[ChatMessage] = Field(
        ..., min_length=1, description="List of messages comprising the conversation so far."
    )
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    n: Optional[int] = Field(1, ge=1, le=10)
    max_tokens: Optional[int] = Field(None, ge=1)
    stream: Optional[bool] = Field(False, description="Whether to stream back partial chunks.")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = None


class CompletionUsage(BaseModel):
    """Token counting breakdown for inference billing and tracking."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionChoice(BaseModel):
    """Individual completion alternative."""

    index: int = 0
    message: ChatMessage
    finish_reason: Optional[str] = "stop"


class ChatCompletionResponse(BaseModel):
    """OpenAI-compliant chat completion non-streaming response schema."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: CompletionUsage
    system_fingerprint: Optional[str] = "ifx_vllm_gateway"


class ChatCompletionChunkDelta(BaseModel):
    """Incremental delta content payload in a streaming chunk."""

    role: Optional[str] = None
    content: Optional[str] = None


class ChatCompletionChunkChoice(BaseModel):
    """Choice payload for streaming chunk."""

    index: int = 0
    delta: ChatCompletionChunkDelta
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    """OpenAI-compliant chat completion streaming event-stream chunk."""

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]


class OpenAIEngineModelCard(BaseModel):
    """OpenAI models endpoint item schema."""

    id: str
    object: str = "model"
    created: int
    owned_by: str = "inferx"
    permission: List[Dict[str, Any]] = []
    root: str
    parent: Optional[str] = None


class OpenAIModelListResponse(BaseModel):
    """OpenAI /v1/models response wrapper."""

    object: str = "list"
    data: List[OpenAIEngineModelCard]
