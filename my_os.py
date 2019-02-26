import os
import time
from typing import Set


def mkdir_p(path):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as exc:
        raise


def current_milli_time() -> int:
    return int(round(time.time() * 1000))


def read_lines(file_path: str) -> Set[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    except OSError:
        print("Could not read " + file_path)
        return set()
