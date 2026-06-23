from collectors.system import get_cpu, get_ram
from collectors.temperature import get_cpu_temp
from collectors.gpu import get_gpu_stats
from collectors.network import get_network
from collectors.battery import get_battery_stats


def safe_cpu():
    cpu = get_cpu()

    return cpu if cpu is not None else 0


def safe_gpu():
    gpu = get_gpu_stats()

    if not gpu:
        return {
            "name": "Unknown GPU",
            "usage": 0,
            "vram_used": 0,
            "vram_total": 0,
            "temp": 0
        }

    return gpu


def get_all_stats():

    return {
        "cpu": safe_cpu(),
        "cpu_temp": get_cpu_temp() or 0,
        "ram": get_ram(),
        "gpu": safe_gpu(),
        "network": get_network(),
        "battery": get_battery_stats()
    }