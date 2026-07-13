import logging
import logging.handlers
import os
import gzip
import shutil
import contextvars
from contextlib import contextmanager

# ─── Context Variables for Request/Session IDs ───
chat_id_var = contextvars.ContextVar("chat_id", default=None)
user_id_var = contextvars.ContextVar("user_id", default=None)

@contextmanager
def log_context(chat_id=None, user_id=None):
    """Context manager to temporarily set logging context variables."""
    tokens = []
    if chat_id is not None:
        tokens.append((chat_id_var, chat_id_var.set(str(chat_id))))
    if user_id is not None:
        tokens.append((user_id_var, user_id_var.set(str(user_id))))
    try:
        yield
    finally:
        for var, token in reversed(tokens):
            var.reset(token)

class CorrelationIdFilter(logging.Filter):
    """Injects chat_id and user_id context variable values into log records."""
    def filter(self, record):
        record.chat_id = chat_id_var.get() or "-"
        record.user_id = user_id_var.get() or "-"
        return True

class ColorFormatter(logging.Formatter):
    """Adds ANSI escape colors to console level names for readability."""
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[1;31m"  # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record):
        orig_levelname = record.levelname
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{orig_levelname:<8}{self.RESET}"
        formatted = super().format(record)
        record.levelname = orig_levelname
        return formatted

# ─── Helper Functions for Automatic Gzip Rotation ───
def gzip_namer(name):
    return name + ".gz"

def gzip_rotator(source, dest):
    with open(source, "rb") as f_in:
        with gzip.open(dest, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(source)

def setup_django_logging():
    """Initializes the logging system and replaces default Django handlers."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logs")
    os.makedirs(log_dir, exist_ok=True)
    
    main_log_file = os.path.join(log_dir, "aman.log")
    
    # 1. Setup Filters
    corr_filter = CorrelationIdFilter()
    
    # 2. Setup Formatters
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | [%(chat_id)s/%(user_id)s] | %(name)s [%(filename)s:%(funcName)s:%(lineno)d] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_formatter = ColorFormatter(
        fmt="%(asctime)s | %(levelname)s | [%(chat_id)s/%(user_id)s] | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # 3. Setup File Handler (Rotating, Gzipped)
    file_handler = logging.handlers.RotatingFileHandler(
        main_log_file, maxBytes=10 * 1024 * 1024, backupCount=7, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(corr_filter)
    file_handler.namer = gzip_namer
    file_handler.rotator = gzip_rotator
    
    # 4. Setup Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(corr_filter)
    
    # 5. Apply to Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Silence chatty third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("django.db.backends").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)

if __name__ == "__main__":
    setup_django_logging()
    logger = get_logger("test_logger")
    with log_context(chat_id="chat123", user_id="user456"):
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        logger.critical("This is a critical message")