import os

# ── Qdrant Connection (shared with RAG + safety) ─────────────────────
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# ── Crisis Keywords (bilingual) ──────────────────────────────────────
CRISIS_KEYWORDS = [
    "اقتل نفسي", "انتحار", "انتحر", "نفسي انتحر", "بدي انتحر", "بده انتحر",
    "بدي أموت", "بدي اموت", "نفسي اموت", "نفسي أموت",
    "أذي نفسي", "اذي نفسي", "اقتل حالي", "أقتل حالي", "رايح اقتل", "راح اقتل",
    "kill myself", "suicide", "self-harm", "end my life", "want to die",
    "hurt myself", "hurt someone", "kill someone", "end it all",
]

# ── Safety System ────────────────────────────────────────────────────
SAFETY_MAX_OUTPUT_RETRIES = 3  # Max retries when response fails validation

# ── LLM Models ───────────────────────────────────────────────────────
# LLM_THINKING_MODEL = "gemma4:31b"    # Higher quality, slower
LLM_THINKING_MODEL = "gemma4:26b"    # Higher quality, slower
LLM_FAST_MODEL = "gemma4:e2b"        # Lower quality, faster
LLM_CONTEXT_WINDOW = 4096   # 8192
LLM_REPEAT_PENALTY = 1.15
LLM_MAX_RETRIES = 3

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

# ── RAG / Knowledge Base ─────────────────────────────────────────────
QDRANT_COLLECTION = "rag_knowledge"
EMBEDDINGS_MODEL = "BAAI/bge-m3"
EMBEDDINGS_VECTOR_SIZE = 1024
EMBEDDINGS_DEVICE = "cuda" # "cpu" or "cuda"
TOP_K_RESULTS = 10 # 3

from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent / "tools" / "rag" / "knowledge"
PDF_DIR = KNOWLEDGE_DIR / "pdfs"
EXCEL_DIR = KNOWLEDGE_DIR / "excel_files"

DATASET_CHUNK_COLUMNS = [
    "Question Title",
    "Question",
    "Answer",
    "Hierarchical Diagnosis",
]

DATASET_COLUMN_LABELS = {
    "Question Title": "العنوان",
    "Question": "السؤال",
    "Answer": "الإجابة",
    "Hierarchical Diagnosis": "التشخيص",
}

DATASET_DROP_COLUMNS = {
    "question number", "question_number", "q number", "q#", "id", "row",
    "doctor", "doctor name", "physician", "specialist", "اسم الطبيب", "الطبيب",
    "date", "location", "city", "country", "التاريخ", "الموقع", "المدينة",
}

PDF_MIN_WORDS = 40
PDF_MAX_WORDS = 350
PDF_OVERLAP_WORDS = 30