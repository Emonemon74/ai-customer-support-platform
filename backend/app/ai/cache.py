"""Tiny in-process TTL + LRU cache for retrieval results.

Identical questions asked against an unchanged conversation re-run the whole
dense + BM25 + rerank pipeline otherwise. The cache is keyed by a per-
conversation version that bumps whenever that conversation's documents change,
so a stale entry is never served after an upload / delete.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict

_MAX_ENTRIES = 256
_TTL_SECONDS = 900.0

_lock = threading.Lock()
_entries: OrderedDict[str, tuple[float, object]] = OrderedDict()
_conversation_version: dict[int, int] = {}


def conversation_version(conversation_id: int) -> int:
    return _conversation_version.get(conversation_id, 0)


def bump_conversation(conversation_id: int) -> None:
    """Invalidate everything cached for a conversation."""
    with _lock:
        _conversation_version[conversation_id] = (
            _conversation_version.get(conversation_id, 0) + 1
        )


def get(key: str):
    now = time.time()
    with _lock:
        hit = _entries.get(key)
        if hit is None:
            return None
        stored_at, value = hit
        if now - stored_at > _TTL_SECONDS:
            del _entries[key]
            return None
        _entries.move_to_end(key)
        return value


def set(key: str, value: object) -> None:
    with _lock:
        _entries[key] = (time.time(), value)
        _entries.move_to_end(key)
        while len(_entries) > _MAX_ENTRIES:
            _entries.popitem(last=False)


def clear() -> None:
    with _lock:
        _entries.clear()
        _conversation_version.clear()
