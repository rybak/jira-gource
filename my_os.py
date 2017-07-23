import os
import time


def mkdir_p(path):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as exc:
        raise


def current_milli_time() -> int:
    return int(round(time.time() * 1000))
