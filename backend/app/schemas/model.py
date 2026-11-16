"""Pydantic Schemas for Model Registry."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ModelBase(BaseModel):
    """Base schema containing shared model attributes."""

    name: str = Field(..., min_length=1, max_length=128, description="Display name of the model")
    repo_id: str = Field(..., min_length=1, max_length=255, description="HuggingFace repo ID or path (e.g. meta-llama/Llama-3.1-8B-Instruct)")
    architecture: str = Field(default="AutoModelForCausalLM", max_length=128, description="Underlying model architecture")
    parameters: str = Field(default="Unknown", max_length=32, description="Parameter scale (e.g. 8B, 70B)")
    context_window: int = Field(default=8192, ge=512, le=1048576, description="Max sequence context window in tokens")
    precision: str = Field(default="BF16", max_length=16, description="Weight precision (e.g. FP16, BF16, INT4, AWQ)")
    size_on_disk_gb: Optional[float] = Field(default=None, ge=0.0, description="Model weight size on disk in gigabytes")
    min_gpu_vram_gb: Optional[float] = Field(default=None, ge=0.0, description="Minimum recommended GPU VRAM in gigabytes")
    local_path: Optional[str] = Field(default=None, max_length=512, description="Local cached filesystem directory path")
    is_downloaded: bool = Field(default=False, description="Whether model weights are resident on local storage")
    tags: List[str] = Field(default_factory=list, description="Categorization tags (e.g. reasoning, coding)")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata and tokenizer configurations")


class ModelCreate(ModelBase):
    """Payload schema for registering a new model."""

    pass


class ModelUpdate(BaseModel):
    """Payload schema for partially updating a registered model."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    architecture: Optional[str] = Field(default=None, max_length=128)
    parameters: Optional[str] = Field(default=None, max_length=32)
    context_window: Optional[int] = Field(default=None, ge=512, le=1048576)
    precision: Optional[str] = Field(default=None, max_length=16)
    size_on_disk_gb: Optional[float] = Field(default=None, ge=0.0)
    min_gpu_vram_gb: Optional[float] = Field(default=None, ge=0.0)
    local_path: Optional[str] = Field(default=None, max_length=512)
    is_downloaded: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata_json: Optional[Dict[str, Any]] = None


class ModelResponse(ModelBase):
    """Response schema representing a persisted model entity."""

    id: str = Field(..., description="Unique UUID identifier")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelListResponse(BaseModel):
    """Paginated list response for registered models."""

    items: List[ModelResponse]
    total: int
    skip: int
    limit: int
