"""
Centralized configuration — all environment variables and settings in one place.
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

# ── Database ─────────────────────────────────────────────────────────
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")

# ── Auth ─────────────────────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "aman-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24  # 24 hours

# ── LLM Models ───────────────────────────────────────────────────────
LLM_THINKING_MODEL = "gemma4:31b"    # Higher quality, slower
LLM_FAST_MODEL = "gemma4:e2b"        # Lower quality, faster
LLM_CONTEXT_WINDOW = 8192
LLM_REPEAT_PENALTY = 1.15

# ── Memory ───────────────────────────────────────────────────────────
MAX_MESSAGES_BEFORE_SUMMARY = 40
