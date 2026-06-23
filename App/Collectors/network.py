import psutil
from ping3 import ping
import threading

_ping_value = 0


def _ping_worker():
    global _ping_value

    while True:
        try:
            p = ping("8.8.8.8", timeout=1)
            _ping_value = round(p * 1000, 1) if p else 0
        except:
            _ping_value = 0


def start_ping_thread():
    thread = threading.Thread(target=_ping_worker, daemon=True)
    thread.start()


def get_network():
    io = psutil.net_io_counters()

    return {
        "upload": round(io.bytes_sent / (1024**2), 2),
        "download": round(io.bytes_recv / (1024**2), 2),
        "ping": _ping_value
    }