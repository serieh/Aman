# ── LLM Models ───────────────────────────────────────────────────────
# LLM_THINKING_MODEL = "gemma4:31b"    # Higher quality, slower
LLM_THINKING_MODEL = "gemma4:26b"    # Higher quality, slower
LLM_FAST_MODEL = "gemma4:e2b"        # Lower quality, faster
LLM_CONTEXT_WINDOW = 4096   # 8192
LLM_REPEAT_PENALTY = 1.15

# ── Memory ───────────────────────────────────────────────────────────
MAX_MESSAGES_BEFORE_SUMMARY = 40

# ── Emotion Estimator ────────────────────────────────────────────────
EMOTION_MODEL = "AnasAlokla/multilingual_go_emotions"
EMOTION_CONFIDENCE_THRESHOLD = 0.05
EMOTION_RELEVANT_LABELS = [
    "neutral",
    "sadness",
    "joy",
    "anger",
    "fear",
    "nervousness",
    "grief",
    "disappointment",
    "remorse",
    "disgust",
    "surprise",
    "confusion",
    "love",
    "gratitude",
    "optimism",
    "embarrassment",
    "caring",
]
