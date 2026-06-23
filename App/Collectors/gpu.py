from pynvml import *
import psutil

_gpu_ready = False


def init_gpu():
    global _gpu_ready
    try:
        nvmlInit()
        _gpu_ready = True
    except:
        _gpu_ready = False


def get_gpu_stats():
    if not _gpu_ready:
        return None

    try:
        handle = nvmlDeviceGetHandleByIndex(0)

        util = nvmlDeviceGetUtilizationRates(handle)
        mem = nvmlDeviceGetMemoryInfo(handle)
        temp = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)

        gpu_usage = util.gpu

        if gpu_usage == 0:
            gpu_usage = psutil.cpu_percent() * 0.3  # estimation

        return {
            "usage": round(gpu_usage, 1),
            "vram_used": round(mem.used / (1024**3), 1),
            "vram_total": round(mem.total / (1024**3), 1),
            "temp": temp or 0
        }

    except:
        return None