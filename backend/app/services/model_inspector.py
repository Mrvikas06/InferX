"""HuggingFace Model Inspection and GPU VRAM Estimation Service."""

import logging
import re
from typing import Any, Dict, Optional, Tuple

import httpx

logger = logging.getLogger("inferx.model_inspector")

# Precision to bytes per parameter mapping
PRECISION_BYTES: Dict[str, float] = {
    "FP32": 4.0,
    "FP16": 2.0,
    "BF16": 2.0,
    "FP8": 1.0,
    "INT8": 1.0,
    "INT4": 0.5,
    "AWQ": 0.5,
    "GPTQ": 0.5,
}


def parse_parameter_count(raw_str: str) -> Tuple[float, str]:
    """Parse parameter count from string (e.g. '8B', '70B', '1.5B', '7B'). Returns (billion_count, clean_str)."""
    match = re.search(r"(\d+(?:\.\d+)?)\s*([BbMm])", raw_str)
    if match:
        val = float(match.group(1))
        unit = match.group(2).upper()
        if unit == "M":
            val = val / 1000.0
        return val, f"{val:.1f}B".replace(".0B", "B")
    return 7.0, "7B"  # Sensible default


def calculate_min_vram_gb(
    parameters_str: str,
    precision: str = "BF16",
    context_window: int = 8192,
) -> float:
    """
    Compute estimated minimum GPU VRAM required to load model weights and serve with KV-cache.
    Formula:
        weights_gb = (params_in_billions * 10^9 * bytes_per_param) / (1024^3)
        kv_cache_overhead = max(2.0, (context_window / 8192) * (params_in_billions * 0.25))
        min_vram = (weights_gb + kv_cache_overhead) * 1.15 (CUDA runtime + PyTorch overhead)
    """
    billion_params, _ = parse_parameter_count(parameters_str)
    bytes_per_param = PRECISION_BYTES.get(precision.upper(), 2.0)

    # Weights size in GiB
    weights_gib = (billion_params * 1e9 * bytes_per_param) / (1024**3)

    # Context window & KV-cache memory allowance
    kv_overhead_gib = max(1.5, (context_window / 8192.0) * (billion_params * 0.2))

    # Total with CUDA activation overhead
    total_required = (weights_gib + kv_overhead_gib) * 1.15
    return round(total_required, 1)


def infer_metadata_from_repo_name(repo_id: str) -> Dict[str, Any]:
    """Heuristic fallback parser when network or HF API is unavailable."""
    name_lower = repo_id.lower()

    # Detect parameters
    param_match = re.search(r"(\d+(?:\.\d+)?[bm])", name_lower)
    param_str = param_match.group(1).upper() if param_match else "7B"

    # Detect precision / quantization
    if "awq" in name_lower:
        precision = "AWQ"
    elif "gptq" in name_lower:
        precision = "GPTQ"
    elif "int4" in name_lower or "q4" in name_lower:
        precision = "INT4"
    elif "fp8" in name_lower:
        precision = "FP8"
    elif "fp16" in name_lower:
        precision = "FP16"
    else:
        precision = "BF16"

    # Detect architecture
    if "llama" in name_lower:
        architecture = "LlamaForCausalLM"
        context_window = 131072 if "3" in name_lower else 4096
    elif "mistral" in name_lower:
        architecture = "MistralForCausalLM"
        context_window = 32768
    elif "qwen" in name_lower:
        architecture = "Qwen2ForCausalLM"
        context_window = 32768
    elif "phi" in name_lower:
        architecture = "Phi3ForCausalLM"
        context_window = 128000
    elif "gemma" in name_lower:
        architecture = "Gemma2ForCausalLM"
        context_window = 8192
    elif "deepseek" in name_lower:
        architecture = "DeepseekV3ForCausalLM"
        context_window = 65536
    else:
        architecture = "AutoModelForCausalLM"
        context_window = 8192

    min_vram = calculate_min_vram_gb(param_str, precision, context_window)
    billion_val, _ = parse_parameter_count(param_str)
    size_on_disk = round((billion_val * 1e9 * PRECISION_BYTES.get(precision, 2.0)) / (1024**3), 1)

    return {
        "name": repo_id.split("/")[-1].replace("-", " "),
        "repo_id": repo_id,
        "architecture": architecture,
        "parameters": param_str,
        "context_window": context_window,
        "precision": precision,
        "size_on_disk_gb": size_on_disk,
        "min_gpu_vram_gb": min_vram,
        "tags": ["llm", "text-generation"],
        "metadata_json": {"source": "heuristic_inference"},
    }


async def inspect_huggingface_repo(repo_id: str, timeout_sec: float = 3.0) -> Dict[str, Any]:
    """
    Query HuggingFace Hub API to extract model architecture, context window, and quantization metadata.
    Falls back gracefully to heuristics if network is unavailable or request times out.
    """
    clean_repo = repo_id.strip()
    config_url = f"https://huggingface.co/{clean_repo}/raw/main/config.json"

    try:
        async with httpx.AsyncClient(timeout=timeout_sec, follow_redirects=True) as client:
            resp = await client.get(config_url)
            if resp.status_code == 200:
                cfg = resp.json()
                architectures = cfg.get("architectures", ["AutoModelForCausalLM"])
                architecture = architectures[0] if architectures else "AutoModelForCausalLM"

                # Extract context window
                context_window = (
                    cfg.get("max_position_embeddings")
                    or cfg.get("seq_length")
                    or cfg.get("sliding_window")
                    or 8192
                )

                # Extract precision / torch_dtype
                torch_dtype = str(cfg.get("torch_dtype", "bfloat16")).lower()
                if "float16" in torch_dtype:
                    precision = "FP16"
                elif "bfloat16" in torch_dtype:
                    precision = "BF16"
                elif "float32" in torch_dtype:
                    precision = "FP32"
                elif "int8" in torch_dtype:
                    precision = "INT8"
                elif "int4" in torch_dtype or "awq" in clean_repo.lower():
                    precision = "AWQ"
                else:
                    precision = "BF16"

                # Quantization config check
                if "quantization_config" in cfg:
                    q_method = cfg["quantization_config"].get("quant_method", "").upper()
                    if q_method in ("AWQ", "GPTQ", "FP8", "BITSANDBYTES"):
                        precision = q_method

                # Determine parameter count from repo_id or config
                heuristics = infer_metadata_from_repo_name(clean_repo)
                parameters = heuristics["parameters"]

                min_vram = calculate_min_vram_gb(parameters, precision, context_window)
                billion_val, _ = parse_parameter_count(parameters)
                size_gb = round((billion_val * 1e9 * PRECISION_BYTES.get(precision, 2.0)) / (1024**3), 1)

                return {
                    "name": clean_repo.split("/")[-1].replace("-", " "),
                    "repo_id": clean_repo,
                    "architecture": architecture,
                    "parameters": parameters,
                    "context_window": int(context_window),
                    "precision": precision,
                    "size_on_disk_gb": size_gb,
                    "min_gpu_vram_gb": min_vram,
                    "tags": ["hf-verified", "causal-lm"],
                    "metadata_json": {
                        "source": "huggingface_api",
                        "model_type": cfg.get("model_type"),
                        "vocab_size": cfg.get("vocab_size"),
                        "num_attention_heads": cfg.get("num_attention_heads"),
                    },
                }

    except Exception as exc:
        logger.info("HuggingFace remote config probe for %s failed (%s); applying heuristic metadata.", clean_repo, exc)

    # Return robust offline heuristic profile
    return infer_metadata_from_repo_name(clean_repo)
