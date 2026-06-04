# safety/crisis_detector.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
import torch

from agent.config import QDRANT_HOST, QDRANT_PORT
from .crisis_keywords import fast_crisis_check, keyword_crisis_hit, pattern_crisis_hit

CRISIS_COLLECTION   = "crisis_knowledge"
CRISIS_THRESHOLD    = 0.75
CRISIS_VECTOR_SIZE  = 384  # all-MiniLM-L6-v2 output size

# Lightweight embedding model for crisis detection only
# Using MiniLM instead of Qwen3-8B — much faster, good enough for similarity
CRISIS_EMBED_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"

_embedder = None
_client   = None


# ─── Lazy Loaders ─────────────────────────────────────────────────────────────

def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _embedder = SentenceTransformer(
            CRISIS_EMBED_MODEL,
            device=device,
            model_kwargs={"use_safetensors": True},
        )
    return _embedder


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
    return _client


# ─── Collection Setup ─────────────────────────────────────────────────────────

def init_crisis_collection():
    """
    Creates the crisis_knowledge collection in Qdrant if it does not exist.
    Run once before populating crisis phrases.
    """
    client = _get_client()
    if not client.collection_exists(CRISIS_COLLECTION):
        client.create_collection(
            collection_name=CRISIS_COLLECTION,
            vectors_config=VectorParams(
                size=CRISIS_VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
        print(f"Created Qdrant collection: {CRISIS_COLLECTION}")
    else:
        print(f"Collection already exists: {CRISIS_COLLECTION}")


def populate_crisis_collection():
    """
    Embeds and stores crisis phrases into the crisis_knowledge collection.
    Run once after init_crisis_collection().
    """
    crisis_phrases = [
        # Arabic
        "اقتل نفسي", "انتحار", "نفسي انتحر", "انتحر", "بدي أموت", "مش قادر أكمل",
        "حياتي ما إلها معنى", "تعبت من الحياة", "بفكر أأذي نفسي",
        "ما في داعي أعيش", "أحسن لو ما كنت موجود",
        "بدي أنهي حياتي", "مش شايف فايدة من الحياة",
        # English
        "kill myself", "suicide", "want to die", "end my life",
        "self-harm", "hurt myself", "no reason to live",
        "better off dead", "can't go on", "want it to be over",
        "life is not worth living", "thinking about suicide",
    ]

    embedder = _get_embedder()
    client   = _get_client()

    vectors = embedder.encode(crisis_phrases, normalize_embeddings=True).tolist()

    points = [
        {"id": i, "vector": vectors[i], "payload": {"phrase": crisis_phrases[i]}}
        for i in range(len(crisis_phrases))
    ]

    client.upsert(collection_name=CRISIS_COLLECTION, points=points)
    print(f"Populated {len(crisis_phrases)} crisis phrases into Qdrant.")


# ─── Gate 1: Keyword Check ────────────────────────────────────────────────────

def _keyword_check(text: str) -> bool:
    """Fast gate — keywords + Arabic verb patterns (works offline)."""
    return fast_crisis_check(text)


# ─── Gate 2: Semantic Check ───────────────────────────────────────────────────

def _semantic_check(text: str) -> bool:
    """
    Deeper second gate — semantic similarity against crisis_knowledge collection.
    Skips gracefully if collection is empty or Qdrant is unreachable.
    """
    try:
        client   = _get_client()
        embedder = _get_embedder()

        # Check collection exists and has vectors
        info = client.get_collection(CRISIS_COLLECTION)
        if info.vectors_count == 0:
            return False

        vector = embedder.encode([text], normalize_embeddings=True)[0].tolist()

        response = client.query_points(
            collection_name=CRISIS_COLLECTION,
            query=vector,
            limit=1,
        )
        results = response.points

        if results and results[0].score >= CRISIS_THRESHOLD:
            return True

    except Exception:
        # Qdrant unreachable or collection missing — fall back silently
        return False

    return False


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def detect_crisis(text: str) -> dict:
    """
    Runs both gates and returns a result dict.
    keyword_triggered: fast match result
    semantic_triggered: deep match result
    crisis_flag: True if either gate fires
    """
    keyword_hit = keyword_crisis_hit(text)
    pattern_hit = False if keyword_hit else pattern_crisis_hit(text)
    fast_hit = keyword_hit or pattern_hit

    # Only run semantic check if fast gates didn't already flag it
    semantic_hit = False if fast_hit else _semantic_check(text)

    crisis_flag = fast_hit or semantic_hit

    return {
        "crisis_flag": crisis_flag,
        "keyword_triggered": keyword_hit,
        "pattern_triggered": pattern_hit,
        "semantic_triggered": semantic_hit,
    }


# ─── Init Runner ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_crisis_collection()
    populate_crisis_collection()
    print("Crisis collection ready.")
