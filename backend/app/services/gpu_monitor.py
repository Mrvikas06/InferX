"""GPU Hardware Telemetry Collector and System Resource Monitor."""

import logging
import os
import time
from typing import List, Optional

import psutil

try:
    from backend.app.schemas.telemetry import GPUStats, SystemResourceStats
except (ImportError, ModuleNotFoundError):
    from app.schemas.telemetry import GPUStats, SystemResourceStats

logger = logging.getLogger("inferx.gpu_monitor")

_NVML_INITIALIZED: bool = False
_NVML_FAILED: bool = False


def _init_nvml() -> bool:
    """Safely initialize NVIDIA Management Library (NVML)."""
    global _NVML_INITIALIZED, _NVML_FAILED
    if _NVML_INITIALIZED:
        return True
    if _NVML_FAILED:
        return False

    try:
        import pynvml
        pynvml.nvmlInit()
        _NVML_INITIALIZED = True
        logger.info("NVML initialized successfully. Hardware GPU metrics active.")
        return True
    except Exception as exc:
        _NVML_FAILED = True
        logger.info("NVML initialization bypassed (%s). Enabling simulated GPU telemetry.", exc)
        return False


def get_gpu_telemetry() -> List[GPUStats]:
    """
    Retrieve real-time GPU telemetry from NVML if available,
    or generate calibrated simulated telemetry.
    """
    if _init_nvml():
        try:
            import pynvml

            count = pynvml.nvmlDeviceGetCount()
            driver_ver = pynvml.nvmlSystemGetDriverVersion()
            if isinstance(driver_ver, bytes):
                driver_ver = driver_ver.decode("utf-8")

            results: List[GPUStats] = []
            for i in range(count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                raw_name = pynvml.nvmlDeviceGetName(handle)
                name = raw_name.decode("utf-8") if isinstance(raw_name, bytes) else str(raw_name)

                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                total_mb = round(float(mem.total) / (1024**2), 1)
                used_mb = round(float(mem.used) / (1024**2), 1)
                free_mb = round(float(mem.free) / (1024**2), 1)
                mem_util_pct = round((used_mb / total_mb) * 100.0, 1) if total_mb > 0 else 0.0

                try:
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_util_pct = float(util.gpu)
                except Exception:
                    gpu_util_pct = 0.0

                try:
                    temp_c = float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
                except Exception:
                    temp_c = None

                try:
                    power_w = round(pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0, 1)
                except Exception:
                    power_w = None

                try:
                    power_limit_w = round(pynvml.nvmlDeviceGetEnforcedPowerLimit(handle) / 1000.0, 1)
                except Exception:
                    power_limit_w = None

                results.append(
                    GPUStats(
                        index=i,
                        name=name,
                        driver_version=str(driver_ver),
                        memory_total_mb=total_mb,
                        memory_used_mb=used_mb,
                        memory_free_mb=free_mb,
                        memory_utilization_pct=mem_util_pct,
                        gpu_utilization_pct=gpu_util_pct,
                        temperature_c=temp_c,
                        power_draw_w=power_w,
                        power_limit_w=power_limit_w,
                        is_simulated=False,
                    )
                )

            if results:
                return results

        except Exception as exc:
            logger.warning("Error reading NVML hardware metrics: %s", exc)

    # Simulated fallback GPU telemetry for non-NVIDIA or dev environments
    now = time.time()
    sim_gpu_util = round(35.0 + 15.0 * (0.5 + 0.5 * (now % 10 - 5) / 5), 1)
    sim_mem_used = round(14200.0 + 800.0 * (now % 6), 1)

    return [
        GPUStats(
            index=0,
            name="NVIDIA A100-SXM4-80GB (Simulated)",
            driver_version="550.54.15",
            memory_total_mb=81920.0,
            memory_used_mb=sim_mem_used,
            memory_free_mb=round(81920.0 - sim_mem_used, 1),
            memory_utilization_pct=round((sim_mem_used / 81920.0) * 100.0, 1),
            gpu_utilization_pct=sim_gpu_util,
            temperature_c=58.5,
            power_draw_w=185.0,
            power_limit_w=400.0,
            is_simulated=True,
        )
    ]


def get_system_resources() -> SystemResourceStats:
    """Retrieve host machine CPU, RAM, and Disk metrics via psutil."""
    cpu_pct = float(psutil.cpu_percent(interval=None))
    cpu_count = psutil.cpu_count(logical=True) or 1

    mem = psutil.virtual_memory()
    ram_total_gb = round(mem.total / (1024**3), 2)
    ram_used_gb = round(mem.used / (1024**3), 2)
    ram_pct = float(mem.percent)

    try:
        disk_path = "C:\\" if os.name == "nt" else "/"
        disk = psutil.disk_usage(disk_path)
        disk_total_gb = round(disk.total / (1024**3), 2)
        disk_used_gb = round(disk.used / (1024**3), 2)
        disk_pct = float(disk.percent)
    except Exception:
        disk_total_gb = 512.0
        disk_used_gb = 128.0
        disk_pct = 25.0

    return SystemResourceStats(
        cpu_utilization_pct=cpu_pct,
        cpu_count=cpu_count,
        ram_total_gb=ram_total_gb,
        ram_used_gb=ram_used_gb,
        ram_utilization_pct=ram_pct,
        disk_total_gb=disk_total_gb,
        disk_used_gb=disk_used_gb,
        disk_utilization_pct=disk_pct,
    )
