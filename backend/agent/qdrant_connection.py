import os
from qdrant_client import QdrantClient

_client = None

def get_shared_qdrant_client() -> QdrantClient:
    """Return a singleton QdrantClient to reuse connections across all modules."""
    global _client
    if _client is None:
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        _client = QdrantClient(host=host, port=port)
    return _client
