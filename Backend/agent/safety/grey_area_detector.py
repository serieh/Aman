# safety/grey_area_detector.py
"""Detect culturally sensitive grey-area topics (not crisis/harm)."""
from __future__ import annotations

import re

from .crisis_keywords import fast_crisis_check
from .grey_area_topics import (
    CATEGORY_LABELS,
    GREY_AREA_KEYWORDS,
    match_grey_categories,
)

# Regex gate — catches dialect / verb forms keywords may miss
_GREY_PATTERNS = [
    # English
    re.compile(
        r"\b(sex|sexual|sexy|rape|raped|rapist|molest|abuse|abused|abuser|"
        r"lgbtq?|gay|lesbian|homosexual|bisexual|transgender|queer|"
        r"cheat(ed|ing)?|affair|adulter|fornicat|masturbat|porn|nude|nudes|"
        r"pregnant|abortion|prostitut|hookup|sexting|onlyfans|"
        r"alcohol|drunk|drugs?|addict(ed|ion)?|cocaine|weed|cannabis|"
        r"gambl|betting|steal|stole|stolen|lied|lying|incest|haram|"
        r"divorc(e|ed|ing)?|infertil|bankrupt|debt|inherit|apostasy|"
        r"atheist|agnostic|criminal|prison|jail|tribal|clan|"
        r"std|sti|herpes|chlamydia|cosmetic|plastic\s*surgery|"
        r"unemployed|fired|dropout|miscarriage|custody)\b",
        re.I,
    ),
    # Arabic — sexuality, sin, shame, substances, family, money, honor
    re.compile(
        r"("
        r"جنس|جنسي|جنسية|اغتص|تحرش|زن[اىيت]|زنا|خيان|"
        r"حرام|ذنب|ندم|عار|فضيح|سمعة|شرف|مكانة\s*اجتماع|"
        r"مثل|lgbt|همجنس|متحول|هوية\s*جندر|"
        r"حمل|حامل|إ?جهاض|اجهاض|عقم|إ?نجاب|"
        r"علاقة\s*سرية|علاقة\s*محرمة|حب\s*حرام|قبل\s*الزواج|"
        r"إ?باح|اباح|عهر|دعار|"
        r"استمن|إ?ستمن|"
        r"خمر|كحول|مخدر|حشيش|إ?دمان|"
        r"قمار|ربا|سرق|ديون|دين|ميراث|ورث|تركة|"
        r"ضرب|عنف|عنف\s*أسر|"
        r"كذ[bp]|"
        r"ضحك\s*عل|رماني|شب\s*و|"
        r"سحر|طلسم|ابتز|"
        r"طلاق|مطلق|زواج\s*قسر|"
        r"سياس|ملحد|لادين|ترك\s*الدين|"
        r"قبلي|عشير|"
        r"سجن|جنائي|محكم|"
        r"تجميل|"
        r"ممتلكات|عقار|"
        r"فشل|رسب|"
        r"أسرار\s*عائل|سر\s*عائل|"
        r"مشاكل\s*(زوج|أبناء|عائل|مال)|"
        r"مرض\s*جنس"
        r")",
        re.I,
    ),
]


def _keyword_check(text: str) -> bool:
    lowered = text.lower()
    return any(kw.lower() in lowered for kw in GREY_AREA_KEYWORDS)


def _pattern_check(text: str) -> bool:
    return any(p.search(text) for p in _GREY_PATTERNS)


def _is_crisis_only_message(text: str, categories: list[str], keyword_hit: bool, pattern_hit: bool) -> bool:
    """Pure suicide/self-harm turns are crisis-only — not grey-area."""
    if not fast_crisis_check(text):
        return False
    return not categories and not keyword_hit and not pattern_hit


def detect_grey_area(text: str) -> dict:
    """
    Returns grey_area_flag, matched categories, and which gate triggered.
    Grey-area is separate from crisis — both can be true when topics mix.
    Suicide/self-harm alone → crisis only (grey_area_flag false).
    """
    empty = {
        "grey_area_flag": False,
        "grey_area_categories": [],
        "keyword_triggered": False,
        "pattern_triggered": False,
        "category_triggered": False,
    }
    if not text or not text.strip():
        return empty

    categories = match_grey_categories(text)
    keyword_hit = _keyword_check(text)
    pattern_hit = False if keyword_hit else _pattern_check(text)
    category_hit = bool(categories)

    if _is_crisis_only_message(text, categories, keyword_hit, pattern_hit):
        return empty

    grey_flag = category_hit or keyword_hit or pattern_hit

    return {
        "grey_area_flag": grey_flag,
        "grey_area_categories": categories,
        "keyword_triggered": keyword_hit,
        "pattern_triggered": pattern_hit,
        "category_triggered": category_hit,
    }


def format_category_hints(category_ids: list[str]) -> str:
    """Human-readable category hint for the system prompt."""
    if not category_ids:
        return ""
    labels = [CATEGORY_LABELS.get(cid, cid) for cid in category_ids[:5]]
    extra = len(category_ids) - len(labels)
    hint = "; ".join(labels)
    if extra > 0:
        hint += f" (+{extra} more)"
    return hint
