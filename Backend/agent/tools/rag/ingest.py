# knowledge/ingest.py
"""
Load → clean → chunk knowledge sources.
Dataset rows: 1 row = 1 chunk (Q&A + diagnosis).
PDFs/URLs: semantic section chunking (paragraph-aware, not random splits).
"""
from __future__ import annotations
import hashlib, re
from typing import Iterable
import pandas as pd
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader, TextLoader
from langchain_core.documents import Document
from pandas.errors import ParserError
from pathlib import Path

from agent.tools.rag.knowledge.loader import get_pdf_sources
from agent.tools.rag.knowledge.URL_SOURCES import URL_SOURCES
from agent.config import (
    DATASET_CHUNK_COLUMNS,
    DATASET_COLUMN_LABELS,
    DATASET_DROP_COLUMNS,
    PDF_MIN_WORDS,
    PDF_MAX_WORDS,
    PDF_OVERLAP_WORDS,
)

pdf_sources = get_pdf_sources()

# ─── Arabic normalization ─────────────────────────────────────────────────────

def normalize_arabic(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[\u0610-\u061A\u064B-\u065F]", "", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ى", "ي", text)
    return text


def _normalize_col(name: str) -> str:
    return re.sub(r"\s+", " ", str(name).strip().lower())


# ─── Text cleaning ────────────────────────────────────────────────────────────

_NOISE_PATTERNS = [
    re.compile(r"^Q\s*#?\s*\d+\.?\s*", re.IGNORECASE),
    re.compile(r"^Question\s*#?\s*\d+\.?\s*", re.IGNORECASE),
    re.compile(r"^رقم\s*السؤال\s*[:：]?\s*\d+\s*", re.IGNORECASE),
    re.compile(r"^Dr\.?\s+[A-Za-z\u0600-\u06FF\s\.]+\s*[-–—]?\s*", re.IGNORECASE),
    re.compile(r"^د\.?\s*[\u0600-\u06FF\s\.]+\s*[-–—]?\s*"),
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    re.compile(r"https?://\S+"),
]


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    for pattern in _NOISE_PATTERNS:
        text = pattern.sub("", text)
    lines: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if len(line.split()) < 3:
            continue
        if line in seen:
            continue
        seen.add(line)
        lines.append(normalize_arabic(line))
    result = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", result).strip()


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _dedupe_documents(docs: list[Document]) -> list[Document]:
    seen: set[str] = set()
    unique: list[Document] = []
    for doc in docs:
        key = _content_hash(doc.page_content)
        if key in seen:
            continue
        seen.add(key)
        unique.append(doc)
    return unique


# ─── Dataset loading ────────────────────────────────────────────────────────────

def _resolve_dataset_columns(df: pd.DataFrame) -> dict[str, str]:
    """Map config column names to actual dataframe columns."""
    mapping: dict[str, str] = {}
    normalized = {_normalize_col(c): c for c in df.columns}
    for wanted in DATASET_CHUNK_COLUMNS:
        key = _normalize_col(wanted)
        if key in normalized:
            mapping[wanted] = normalized[key]
    return mapping


def _row_is_empty(row: pd.Series, col_map: dict[str, str]) -> bool:
    for logical, actual in col_map.items():
        if logical in ("Question", "Answer"):
            val = str(row.get(actual, "")).strip()
            if val and val.lower() != "nan":
                return False
    return True


def load_datasets(csv_sources: dict) -> list[Document]:
    """
    Each valid row becomes one chunk with diagnosis + Q&A fields.
    Drops duplicates, empty rows, and metadata columns (doctor, date, etc.).
    """
    docs: list[Document] = []
    for name, path in csv_sources.items():
        print(f"Loading dataset [{name}]: {path}")
        try:
            if str(path).lower().endswith((".xlsx", ".xls")):
                try:
                    df = pd.read_excel(path)
                except ImportError as exc:
                    raise RuntimeError(
                        "Excel support requires openpyxl. Install: uv pip install openpyxl"
                    ) from exc
            else:
                try:
                    df = pd.read_csv(path, encoding="utf-8")
                except (UnicodeDecodeError, ParserError):
                    df = pd.read_csv(path, encoding="windows-1256", engine="python")
        except Exception as exc:
            print(f"  Skipping {path}: {exc}")
            continue

        drop_cols = [
            c for c in df.columns if _normalize_col(c) in DATASET_DROP_COLUMNS
        ]
        if drop_cols:
            df = df.drop(columns=drop_cols, errors="ignore")

        col_map = _resolve_dataset_columns(df)
        if "Question" not in col_map or "Answer" not in col_map:
            print(f"  Skipping {name}: missing Question/Answer columns")
            continue

        for _, row in df.iterrows():
            if _row_is_empty(row, col_map):
                continue
            parts: list[str] = []
            for logical in DATASET_CHUNK_COLUMNS:
                actual = col_map.get(logical)
                if not actual:
                    continue
                value = clean_text(str(row[actual]))
                if not value or value.lower() == "nan":
                    continue
                label = DATASET_COLUMN_LABELS.get(logical, logical)
                parts.append(f"{label}: {value}")
            if not parts:
                continue
            combined = "\n".join(parts)
            if len(combined.split()) < 8:
                continue
            docs.append(
                Document(
                    page_content=combined,
                    metadata={
                        "source_name": name,
                        "source_type": "dataset_qa",
                        "chunk_strategy": "one_row",
                    },
                )
            )
    print(f"Loaded {len(docs)} dataset Q&A chunks.")
    return docs


# ─── PDF / URL loading ────────────────────────────────────────────────────────

def load_pdfs(pf_sources: dict) -> list[Document]:
    docs: list[Document] = []
    for name, path in pf_sources.items():
        print(f"Loading PDF [{name}]: {path}")
        try:
            loader = PyPDFLoader(path)
            pages = loader.load()
        except Exception as exc:
            print(f"  Skipping {path}: {exc}")
            continue
        for page in pages:
            cleaned = clean_text(page.page_content)
            if len(cleaned.split()) < PDF_MIN_WORDS:
                continue
            page.page_content = cleaned
            page.metadata["source_name"] = name
            page.metadata["source_type"] = "pdf"
            docs.append(page)
    return docs


def load_urls(url_sources: dict) -> list[Document]:
    docs: list[Document] = []
    for name, url in url_sources.items():
        print(f"Loading URL [{name}]: {url}")
        try:
            loader = WebBaseLoader(url)
            pages = loader.load()
        except Exception as exc:
            print(f"  Skipping {url}: {exc}")
            continue
        for page in pages:
            cleaned = clean_text(page.page_content)
            if len(cleaned.split()) < PDF_MIN_WORDS:
                continue
            page.page_content = cleaned
            page.metadata["source_name"] = name
            page.metadata["source_type"] = "url"
            docs.append(page)
    return docs


def load_text_files() -> list[Document]:
    docs: list[Document] = []
    knowledge_dir = Path(__file__).parent / "knowledge"
    for file_path in knowledge_dir.glob("*.md"):
        print(f"Loading Markdown [{file_path.name}]: {file_path}")
        try:
            loader = TextLoader(str(file_path), encoding="utf-8")
            pages = loader.load()
        except Exception as exc:
            print(f"  Skipping {file_path}: {exc}")
            continue
        for page in pages:
            cleaned = clean_text(page.page_content)
            if len(cleaned.split()) < PDF_MIN_WORDS:
                continue
            page.page_content = cleaned
            page.metadata["source_name"] = file_path.stem
            page.metadata["source_type"] = "markdown"
            docs.append(page)
    return docs


# ─── Semantic chunking (PDFs / URLs) ─────────────────────────────────────────

def _split_paragraphs(text: str) -> list[str]:
    blocks = re.split(r"\n\s*\n", text)
    return [b.strip() for b in blocks if b.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


def _chunk_words(words: list[str], max_words: int, overlap: int) -> Iterable[list[str]]:
    if not words:
        return
    start = 0
    n = len(words)
    while start < n:
        end = min(start + max_words, n)
        yield words[start:end]
        if end >= n:
            break
        start = max(end - overlap, start + 1)


def semantic_chunk_text(
    text: str,
    source_name: str,
    source_type: str,
    min_words: int = PDF_MIN_WORDS,
    max_words: int = PDF_MAX_WORDS,
    overlap_words: int = PDF_OVERLAP_WORDS,
) -> list[Document]:
    """
    Build chunks from paragraphs and headings — keeps complete ideas together.
    """
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return []

    buffer: list[str] = []
    buffer_words = 0
    chunks: list[Document] = []

    def flush_buffer() -> None:
        nonlocal buffer, buffer_words
        if not buffer:
            return
        combined = "\n\n".join(buffer).strip()
        wc = _word_count(combined)
        if wc < min_words:
            buffer = []
            buffer_words = 0
            return
        if wc <= max_words:
            chunks.append(
                Document(
                    page_content=combined,
                    metadata={
                        "source_name": source_name,
                        "source_type": source_type,
                        "chunk_strategy": "semantic",
                    },
                )
            )
        else:
            words = combined.split()
            for piece in _chunk_words(words, max_words, overlap_words):
                piece_text = " ".join(piece).strip()
                if _word_count(piece_text) >= min_words:
                    chunks.append(
                        Document(
                            page_content=piece_text,
                            metadata={
                                "source_name": source_name,
                                "source_type": source_type,
                                "chunk_strategy": "semantic_split",
                            },
                        )
                    )
        buffer = []
        buffer_words = 0

    for para in paragraphs:
        wc = _word_count(para)
        if wc > max_words:
            flush_buffer()
            for piece in _chunk_words(para.split(), max_words, overlap_words):
                piece_text = " ".join(piece).strip()
                if _word_count(piece_text) >= min_words:
                    chunks.append(
                        Document(
                            page_content=piece_text,
                            metadata={
                                "source_name": source_name,
                                "source_type": source_type,
                                "chunk_strategy": "semantic_split",
                            },
                        )
                    )
            continue
        if buffer_words + wc > max_words and buffer:
            flush_buffer()
        buffer.append(para)
        buffer_words += wc

    flush_buffer()
    return chunks


def chunk_publication_documents(docs: list[Document]) -> list[Document]:
    """Apply semantic chunking to PDF/URL documents only."""
    chunked: list[Document] = []
    for doc in docs:
        source_type = doc.metadata.get("source_type", "pdf")
        if source_type == "dataset_qa":
            chunked.append(doc)
            continue
        source_name = doc.metadata.get("source_name", "unknown")
        chunked.extend(
            semantic_chunk_text(
                doc.page_content,
                source_name=source_name,
                source_type=source_type,
            )
        )
    return chunked


# ─── Main entry ───────────────────────────────────────────────────────────────

def ingest(
    pdf_sources: dict = pdf_sources,
    url_sources: dict = URL_SOURCES,
    # csv_sources: dict = CSV_SOURCES,
) -> list[Document]:
    """Load → clean → chunk. Returns documents ready for embedding."""
    docs: list[Document] = []
    # docs.extend(load_datasets(csv_sources))
    docs.extend(load_pdfs(pdf_sources))
    docs.extend(load_urls(url_sources))
    docs.extend(load_text_files())

    chunks = chunk_publication_documents(docs)
    chunks = _dedupe_documents(chunks)
    print(f"Ingest complete: {len(chunks)} clean chunks ready.")
    return chunks
