import torch, textwrap
import functools
from collections import defaultdict
from transformers import pipeline

from logger import get_logger
from agent.config import EMOTION_MODEL, EMOTION_CONFIDENCE_THRESHOLD, EMOTION_RELEVANT_LABELS

logger = get_logger(__name__)

logger.info(f"Loading emotion estimation model | model: {EMOTION_MODEL}")

_device = 0 if torch.cuda.is_available() else -1
_device_name = "CUDA" if _device == 0 else "CPU"
logger.info(f"Emotion estimator device: {_device_name}")

_classifier = pipeline(
    "text-classification",
    model=EMOTION_MODEL,
    top_k=None,
    device=_device,
    truncation=True,
)

logger.info("Emotion estimation model loaded successfully")

_relevant_set = set(EMOTION_RELEVANT_LABELS)



@functools.lru_cache(maxsize=1000)
def estimate_emotion(text: str) -> dict:
    """
    Run the pretrained emotion classifier on the given text.
    Chunks the text to handle any input size safely.

    Returns a dict mapping each relevant emotion label to its average confidence
    score (0.0-1.0) across all chunks. Only emotions above EMOTION_CONFIDENCE_THRESHOLD
    and in EMOTION_RELEVANT_LABELS are included.

    Example: {"sadness": 0.72, "fear": 0.41, "neutral": 0.08}
    """
    try:
        if not text.strip():
            return {"neutral": 1.0}

        # Chunk the text to avoid token limits (400 chars is safely < 512 tokens)
        chunks = textwrap.wrap(text, width=400, break_long_words=False)
        if not chunks:
            chunks = [text]

        # Run pipeline on all chunks (batching)
        chunk_results = _classifier(chunks)
        
        # Aggregate scores
        aggregated_scores = defaultdict(float)
        
        for scores in chunk_results:
            # scores is a list of {"label": ..., "score": ...}
            for item in scores:
                aggregated_scores[item["label"]] += item["score"]
                
        # Average the scores
        num_chunks = len(chunks)
        filtered = {
            label: round(total_score / num_chunks, 4)
            for label, total_score in aggregated_scores.items()
            if label in _relevant_set and (total_score / num_chunks) >= EMOTION_CONFIDENCE_THRESHOLD
        }

        # Sort by confidence descending
        filtered = dict(sorted(filtered.items(), key=lambda x: x[1], reverse=True))

        # Down-weight neutral if a strong emotion is present
        strong_emotions = ["sadness", "anger", "fear", "grief", "disappointment", "remorse", "disgust", "nervousness"]
        if any(e in filtered and filtered[e] >= 0.10 for e in strong_emotions) and "neutral" in filtered:
            filtered["neutral"] = round(filtered["neutral"] * 0.1, 4)
            if filtered["neutral"] < EMOTION_CONFIDENCE_THRESHOLD:
                del filtered["neutral"]
            filtered = dict(sorted(filtered.items(), key=lambda x: x[1], reverse=True))

        # top_emotion = next(iter(filtered), "neutral")
        # top_score = filtered.get(top_emotion, 0.0)
        logger.debug(f"Emotion estimated | chunks: {num_chunks} | total_labels: {len(filtered)}")

        return filtered

    except Exception as e:
        logger.error(f"Emotion estimation failed | error: {str(e)}")
        return {"neutral": 1.0}
