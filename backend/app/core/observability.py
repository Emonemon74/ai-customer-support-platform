"""Lightweight observability: request-scoped context, structured logging and
in-process counters.

Deliberately dependency-free. The roadmap's rule is "start simple, add a full
stack (OpenTelemetry/Prometheus) only when useful" -- this gives every log line
a request id and the key latency/token numbers, plus a ``/metrics`` snapshot.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from contextvars import ContextVar

_context: ContextVar[dict] = ContextVar("request_context", default={})

# Fields promoted into every log line (see ContextFilter).
_LOG_FIELDS = ("request_id", "user_id", "conversation_id", "document_id", "job_id")


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def set_context(**fields) -> None:
    """Merge fields into the current request context."""
    current = dict(_context.get())
    for key, value in fields.items():
        if value is not None:
            current[key] = value
    _context.set(current)


def get_context() -> dict:
    return dict(_context.get())


def reset_context(token) -> None:
    _context.reset(token)


def bind_context(**fields):
    _context.set(dict(fields))


class ContextFilter(logging.Filter):
    """Attach request-context fields to each record so the formatter can show
    them. Missing fields render as ``-``."""

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = _context.get()
        for field in _LOG_FIELDS:
            setattr(record, field, ctx.get(field, "-"))
        return True


def configure_logging() -> None:
    fmt = (
        "%(asctime)s | %(levelname)s | %(name)s | "
        "req=%(request_id)s user=%(user_id)s conv=%(conversation_id)s | %(message)s"
    )
    root = logging.getLogger()
    for handler in root.handlers:
        handler.setFormatter(logging.Formatter(fmt))
        handler.addFilter(ContextFilter())


# --------------------------------------------------------------------------- #
# Metrics: counters + latency summaries (count/sum), Prometheus text format.
# --------------------------------------------------------------------------- #
class _Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, tuple], float] = {}
        self._summaries: dict[tuple[str, tuple], list[float]] = {}

    def inc(self, name: str, value: float = 1.0, **labels) -> None:
        key = (name, tuple(sorted(labels.items())))
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + value

    def observe(self, name: str, value: float, **labels) -> None:
        key = (name, tuple(sorted(labels.items())))
        with self._lock:
            bucket = self._summaries.setdefault(key, [0.0, 0.0])
            bucket[0] += 1
            bucket[1] += value

    def render(self) -> str:
        lines: list[str] = []
        with self._lock:
            for (name, labels), value in sorted(self._counters.items()):
                lines.append(f"{name}{_fmt_labels(labels)} {value}")
            for (name, labels), (count, total) in sorted(self._summaries.items()):
                lines.append(f"{name}_count{_fmt_labels(labels)} {count}")
                lines.append(f"{name}_sum{_fmt_labels(labels)} {total}")
        return "\n".join(lines) + "\n"


def _fmt_labels(labels: tuple) -> str:
    if not labels:
        return ""
    inner = ",".join(f'{k}="{v}"' for k, v in labels)
    return "{" + inner + "}"


metrics = _Metrics()


class Timer:
    """``with Timer() as t: ...`` then ``t.ms``."""

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        self.ms = 0.0
        return self

    def __exit__(self, *exc) -> None:
        self.ms = (time.perf_counter() - self._start) * 1000
