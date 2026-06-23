import threading
import time

from engine import get_all_stats

_latest_stats = {}
_lock = threading.Lock()


def update_loop():
    global _latest_stats

    while True:
        try:
            data = get_all_stats()

            with _lock:
                _latest_stats = data

        except Exception as e:
            print("Cache error:", e)

        time.sleep(1)


def start_cache():
    thread = threading.Thread(
        target=update_loop,
        daemon=True
    )
    thread.start()


def get_cached_stats():
    with _lock:
        return _latest_stats.copy()