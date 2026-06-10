import time
from collections import OrderedDict


TTL = 3600


_cache: OrderedDict[str, tuple[float, list[dict]]] = OrderedDict()


def get(key: str) -> list[dict] | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    ts, data = entry
    if time.time() - ts > TTL:
        del _cache[key]
        return None
    return data


def set(key: str, data: list[dict]) -> None:
    _cache[key] = (time.time(), data)


def clear(key: str | None = None) -> None:
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()
