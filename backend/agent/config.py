# ── Crisis Keywords (bilingual) ──────────────────────────────────────
CRISIS_KEYWORDS = [
    "اقتل نفسي", "انتحار", "انتحر", "نفسي انتحر", "بدي انتحر", "بده انتحر",
    "بدي أموت", "بدي اموت", "نفسي اموت", "نفسي أموت",
    "أذي نفسي", "اذي نفسي", "اقتل حالي", "أقتل حالي", "رايح اقتل", "راح اقتل",
    "kill myself", "suicide", "self-harm", "end my life", "want to die",
    "hurt myself", "hurt someone", "kill someone", "end it all",
]

# ── Safety System ────────────────────────────────────────────────────
SAFETY_MAX_OUTPUT_RETRIES = 3
FALLBACK_RESPONSE = {
    "content": "I'm here with you. Could you tell me a little more about what's on your mind?",
    "emotional_state": {"emotion": "unknown", "confidence": 0.0},
}

# ── LLM Models ───────────────────────────────────────────────────────
LLM_MAX_RETRIES = 3
DYNAMIC_CONTEXT_WINDOW = True

# LLM FAST
LLM_FAST_MODEL = "gemma4:e2b"   # danielsheep/gpt-oss-20b-Unsloth:latest
LLM_FAST_CONTEXT_WINDOW = 4096
LLM_FAST_KEEP_ALIVE = -1
LLM_FAST_REPEAT_PENALTY = 1.2
LLM_FAST_THINK = False

# Thinking LLMs
LLM_THINKING_MODEL_NAME = "openai/gpt-oss-120b"
LLM_THINKING_SECONDARY_MODEL_NAME = "llama-3.3-70b-versatile"
LLM_THINKING_MAX_TOKENS = 2048
LLM_THINKING_MAX_RETRIES = 1

hard_refusal_patterns = [
    "cannot fulfill", "unable to provide", "i apologize, but i cannot", 
    "i must decline", "i cannot engage", "i am not able to", 
    "it would be inappropriate", "i must refrain",
    "لا أستطيع", "لا يمكنني", "أعتذر، لا يمكنني", "أنا غير قادر على"
]

soft_disclaimers = [
    "As an AI language model, ",
    "I want to be transparent that I am an AI. ",
    "Please note that I am an AI and not a medical professional. "
]

# ── Memory ───────────────────────────────────────────────────────────
MAX_MESSAGES_BEFORE_SUMMARY = 25
QDRANT_USER_COLLECTION = "user_memory"

# ── Emotion Estimator ────────────────────────────────────────────────
EMOTION_CASHE_SIZE = 1000
EMOTION_MODEL = "AnasAlokla/multilingual_go_emotions"
EMOTION_CONFIDENCE_THRESHOLD = 0.05
CHUNK_SIZE = 400
STRONG_EMOTIONS_THRESHOLD = 0.10

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
STRONG_EMOTIONS = ["sadness", "anger", "fear", "grief", "disappointment", "remorse", "disgust", "nervousness"]

# ── RAG / Knowledge Base ─────────────────────────────────────────────
QDRANT_COLLECTION = "rag_knowledge"
EMBEDDINGS_MODEL = "BAAI/bge-m3"
EMBEDDINGS_VECTOR_SIZE = 1024
EMBEDDINGS_DEVICE = "cuda" # "cpu" or "cuda"
TOP_K_RESULTS = 3
EMBEDDING_CACHE_SIZE = 5000

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