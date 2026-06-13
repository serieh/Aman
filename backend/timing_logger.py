"""
Timing Logger — writes operation durations to a separate log file.

Usage:
    from timing_logger import timed_operation

    # As a context manager
    with timed_operation("emotion_estimation", chat_id="abc"):
        result = estimate_emotion(text)

    # The timing log entry will look like:
    # 2026-06-12 13:17:39 | emotion_estimation | 42.3ms | OK | chat_id=abc
"""

import time
import asyncio
import logging
import os
import functools
from datetime import datetime
from contextlib import contextmanager

# ── Use the same run-timestamp as the main logger for easy correlation ──
if "AMAN_LOG_TIMESTAMP" not in os.environ:
    os.environ["AMAN_LOG_TIMESTAMP"] = datetime.now().strftime("%Y%m%d_%H:%M:%S")

_RUN_TIMESTAMP = os.environ["AMAN_LOG_TIMESTAMP"]
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_TIMING_LOG_FILE = os.path.join(_LOG_DIR, f"timing_{_RUN_TIMESTAMP}.log")

# ── Dedicated logger that only writes to the timing file ──
_timing_logger = logging.getLogger("aman.timing")
_timing_logger.setLevel(logging.INFO)
_timing_logger.propagate = False  # don't leak into the root/console logger

if not _timing_logger.handlers:
    _fh = logging.FileHandler(_TIMING_LOG_FILE, encoding="utf-8")
    _fh.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    _timing_logger.addHandler(_fh)


@contextmanager
def timed_operation(name: str, **meta):
    """Context manager that logs wall-clock duration of the enclosed block.

    Example:
        with timed_operation("llm_inference", chat_id=chat_id):
            response = await llm.ainvoke(messages)
    """
    start = time.perf_counter()
    status = "OK"
    try:
        yield
    except Exception as e:
        status = f"ERROR: {type(e).__name__}: {e}"
        raise
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        meta_str = " | ".join(f"{k}={v}" for k, v in meta.items()) if meta else ""
        parts = [name, f"{elapsed_ms:.1f}ms", status]
        if meta_str:
            parts.append(meta_str)
        _timing_logger.info(" | ".join(parts))


def timed(name: str):
    """Decorator version of timed_operation for simple functions.

    Example:
        @timed("emotion_estimation")
        def estimate_emotion(text):
            ...
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with timed_operation(name):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with timed_operation(name):
                    return func(*args, **kwargs)
            return sync_wrapper
    return decorator
