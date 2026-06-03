# knowledge/embeddings.py
"""BGE-M3 embeddings + Qdrant ingestion"""
from __future__ import annotations
import os
from typing import Any
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config import (
    EMBEDDINGS_DEVICE,
    EMBEDDINGS_MODEL,
    EMBEDDINGS_VECTOR_SIZE,
    QDRANT_COLLECTION
)
from ingest import ingest
from knowledge.URL_SOURCES import URL_SOURCES
from knowledge.loader import get_pdf_sources

_EMBEDDING_MODEL: HuggingFaceEmbeddings | None = None
pdf_sources = get_pdf_sources()
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
HF_TOKEN = os.getenv("HF_TOKEN")


def get_embedding_model(
    model_name: str = EMBEDDINGS_MODEL,
    device: str = EMBEDDINGS_DEVICE,
) -> HuggingFaceEmbeddings:
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL

    model_kwargs: dict[str, Any] = {
        "device": device,
        # Avoid torch.load on .bin files (requires torch>=2.6); safetensors is safe.
        "model_kwargs": {"use_safetensors": True},
    }
    if HF_TOKEN:
        model_kwargs["token"] = HF_TOKEN

    batch_size = int(os.getenv("EMBEDDINGS_BATCH_SIZE", "16"))
    _EMBEDDING_MODEL = HuggingFaceEmbeddings(
        model_name=os.getenv("EMBEDDINGS_MODEL", model_name),
        model_kwargs=model_kwargs,
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": batch_size,
        },
    )
    return _EMBEDDING_MODEL


def _get_qdrant_url() -> str:
    return f"http://{QDRANT_HOST}:{QDRANT_PORT}"


def ensure_qdrant_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int = EMBEDDINGS_VECTOR_SIZE,
) -> None:
    if client.collection_exists(collection_name):
        return
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )


def _resolve_vector_size(embedding_model: HuggingFaceEmbeddings) -> int:
    vector = embedding_model.embed_query("vector_size_probe")
    return len(vector)


def ingest_sources_to_qdrant(
    collection_name: str = QDRANT_COLLECTION,
    recreate: bool = False,
    pdf_sources: dict = pdf_sources,
    url_sources: dict = URL_SOURCES,
    # csv_sources: dict = CSV_SOURCES,
) -> QdrantVectorStore:
    docs = ingest(pdf_sources=pdf_sources, url_sources=url_sources)  # , csv_sources=csv_sources)
    if not docs:
        raise ValueError("No documents were loaded from the configured sources.")

    embedding_model = get_embedding_model()
    vector_size = _resolve_vector_size(embedding_model)

    client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
    if recreate:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
    else:
        ensure_qdrant_collection(client, collection_name, vector_size=vector_size)

    batch_size = int(os.getenv("QDRANT_UPSERT_BATCH_SIZE", "32"))
    vectorstore = QdrantVectorStore.from_documents(
        docs,
        embedding_model,
        location=_get_qdrant_url(),
        collection_name=collection_name,
        batch_size=batch_size,
    )
    print(f"Stored {len(docs)} chunks in Qdrant collection '{collection_name}'.")
    return vectorstore

get_qwen_embedding_model = get_embedding_model
