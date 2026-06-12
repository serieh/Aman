# agents/rag.py
from __future__ import annotations
from typing import Any
from agent.qdrant_connection import get_shared_qdrant_client
from ...config import QDRANT_COLLECTION, TOP_K_RESULTS
from . import embeddings

_EMBEDDING_MODEL: Any | None = None


def _get_embedding_model() -> Any:
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        _EMBEDDING_MODEL = embeddings.get_embedding_model()
    return _EMBEDDING_MODEL


def _extract_payload_text(payload: dict[str, Any]) -> str | None:
    for key in ("text", "page_content", "content"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def run_rag(query: str, top_k: int = TOP_K_RESULTS) -> dict:
    if not query or not query.strip():
        return {"passages": [], "error": "empty_query"}

    try:
        client = get_shared_qdrant_client()
        if not client.collection_exists(QDRANT_COLLECTION):
            return {"passages": [], "error": "collection_missing"}

        embedder = _get_embedding_model()
        if hasattr(embedder, "embed_query"):
            vector = embedder.embed_query(query)
        else:
            vector = embedder.embed_documents([query])[0]

        response = client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=vector,
            limit=top_k,
        )
        results = response.points

        passages: list[str] = []
        for point in results:
            payload = point.payload or {}
            text = _extract_payload_text(payload)
            if text:
                passages.append(text)

        return {"passages": passages, "error": None}
    except Exception as exc:
        return {"passages": [], "error": str(exc)}
