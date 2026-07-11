import logging
import os
from datetime import datetime

# ── Generate a unique log filename once at import time (= once per run) ──
if "AMAN_LOG_TIMESTAMP" not in os.environ:
    os.environ["AMAN_LOG_TIMESTAMP"] = datetime.now().strftime("%Y%m%d_%H:%M:%S")
_RUN_TIMESTAMP = os.environ["AMAN_LOG_TIMESTAMP"]
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, f"aman_{_RUN_TIMESTAMP}.log")


def get_logger(name: str) -> logging.Logger:
    """Return a named logger that writes to both console and a per-run log file.

    Log file: Logs/aman_<YYYYMMDD>_<HHMMSS>.log  (one per application run)
    """
    logger = logging.getLogger(name)

    if not logger.handlers:  # prevent duplicate handlers if called multiple times
        logger.setLevel(logging.DEBUG)

        # ── File handler – detailed output for post-mortem debugging ──
        file_formatter = logging.Formatter(
            fmt=(
                "%(asctime)s | %(levelname)-8s | %(name)s "
                "[%(filename)s:%(funcName)s:%(lineno)d] | %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)

        # ── Console handler – concise, easy-to-scan output ──
        console_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


if __name__ == "__main__":
    logger = get_logger("test_logger")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    print(f"\n→ Log written to: {_LOG_FILE}")