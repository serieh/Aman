# safety/crisis_keywords.py
"""Fast crisis keyword + pattern matching (no Qdrant, no embeddings)."""
from __future__ import annotations

import re

from agent.config import CRISIS_KEYWORDS

# Arabic dialect verb/noun forms missed by exact keyword lists (e.g. انتحر vs انتحار)
CRISIS_PATTERNS = [
    re.compile(r"انتح[ار]", re.I),  # انتحر، انتحار، انتحرت
    re.compile(r"نفسي\s*انتح", re.I),
    re.compile(r"بد[iyee]\s*انتح", re.I),
    re.compile(r"بده\s*انتح", re.I),
    re.compile(r"را[iy]ح\s*انتح", re.I),
    re.compile(r"اقتل\s*(نفس|حال)", re.I),
    re.compile(r"أ?(?:ذي|أذي)\s*نفس", re.I),
    re.compile(r"\b(kill\s+myself|end\s+my\s+life|want\s+to\s+die)\b", re.I),
]


def keyword_crisis_hit(text: str) -> bool:
    lowered = text.lower()
    return any(kw.lower() in lowered for kw in CRISIS_KEYWORDS)


def pattern_crisis_hit(text: str) -> bool:
    return any(p.search(text) for p in CRISIS_PATTERNS)


def fast_crisis_check(text: str) -> bool:
    """Keyword or regex gate — must work even when Qdrant is offline."""
    if not text or not text.strip():
        return False
    return keyword_crisis_hit(text) or pattern_crisis_hit(text)
