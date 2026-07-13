import time
import os
import logging
import logging.handlers
from datetime import datetime
from contextlib import contextmanager
from logger import gzip_namer, gzip_rotator, CorrelationIdFilter

_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_TIMING_LOG = os.path.join(_LOG_DIR, "timing.log")

_timing_logger = logging.getLogger("aman.timing")
_timing_logger.setLevel(logging.INFO)
_timing_logger.propagate = False

if not _timing_logger.handlers:
    # Timing File Handler (Rotating & Gzipped)
    _fh = logging.handlers.RotatingFileHandler(
        _TIMING_LOG, maxBytes=10 * 1024 * 1024, backupCount=7, encoding="utf-8"
    )
    _fh.namer = gzip_namer
    _fh.rotator = gzip_rotator
    
    corr_filter = CorrelationIdFilter()
    _fh.addFilter(corr_filter)
    
    _fh.setFormatter(logging.Formatter(
        fmt="%(asctime)s | [%(chat_id)s/%(user_id)s] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    _timing_logger.addHandler(_fh)

@contextmanager
def timed_operation(name: str, **meta):
    """Context manager that logs wall-clock duration of the enclosed block."""
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
        
        # Log to timing.log
        _timing_logger.info(" | ".join(parts))
        
        # Log summary statement to main log for easy correlation
        main_logger = logging.getLogger("timing_summary")
        main_logger.debug(f"Operation timed: {name} took {elapsed_ms:.1f}ms (Status: {status})")

def timed(name: str):
    """Decorator version of timed_operation for simple functions."""
    import asyncio
    import functools
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
