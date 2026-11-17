"""Model Weights Storage, Filesystem Caching, and Download Verification Service."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Bootstrap sys.path to ensure InferX root is resolvable in all runtime contexts
_repo_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from backend.app.core.config import BASE_DIR, get_settings

settings = get_settings()

DEFAULT_MODELS_DIR = BASE_DIR / "models"


def get_model_cache_path(repo_id: str) -> Path:
    """Derive local filesystem directory path for a HuggingFace repository."""
    normalized_name = repo_id.replace("/", "--")
    return DEFAULT_MODELS_DIR / normalized_name


def check_local_weights(
    repo_id: str,
    custom_path: Optional[str] = None,
) -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Check if model weights exist on disk.
    Returns (is_downloaded, resolved_path, size_on_disk_gb).
    """
    target_dir = Path(custom_path) if custom_path else get_model_cache_path(repo_id)

    if not target_dir.exists() or not target_dir.is_dir():
        return False, str(target_dir), None

    # Check for weight artifacts: safetensors, bin, or gguf files
    weight_files = list(target_dir.glob("*.safetensors")) + list(target_dir.glob("*.bin")) + list(target_dir.glob("*.gguf"))
    if not weight_files:
        return False, str(target_dir), None

    total_bytes = sum(f.stat().st_size for f in weight_files)
    total_gb = round(total_bytes / (1024**3), 2)
    return True, str(target_dir), total_gb


def register_local_weights(
    repo_id: str,
    target_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify and register local filesystem residency."""
    is_down, resolved_path, size_gb = check_local_weights(repo_id, target_path)
    return {
        "repo_id": repo_id,
        "is_downloaded": is_down,
        "local_path": resolved_path,
        "size_on_disk_gb": size_gb,
    }
