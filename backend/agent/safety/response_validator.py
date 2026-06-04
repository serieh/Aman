# safety/response_validator.py
"""Output safety — block harmful advice and routing scripts; allow grey-area vocabulary."""
from __future__ import annotations

import re

# Always block instructive self-harm (not topic words like طلاق or انتحار in empathetic context)
INSTRUCTIVE_HARM_PHRASES = [
    "kill yourself", "end your life", "hurt yourself",
    "you should die", "go kill yourself",
    "اقتل نفسك", "أذِ نفسك", "اذي نفسك", "اذبح نفسك",
    "يجب أن تموت", "روح انتحر",
]

DIAGNOSIS_PHRASES = [
    "you have depression", "you are bipolar", "you have anxiety disorder",
    "أنت مصاب", "تشخيصك", "عندك اكتئاب", "عندك مرض",
    "take this medication", "stop your medication", "increase your dose",
    "خذ هذا الدواء", "وقف الدواء",
]

REFUSAL_PHRASES = [
    "i can't discuss", "i cannot discuss", "i won't discuss",
    "لا أستطيع مناقشة", "لا يمكنني مناقشة", "لن أناقش",
]

REFUSAL_PATTERNS = [
    "as an ai, i can't",
    "as an ai, i cannot",
    "i'm not able to help with that",
    "this is inappropriate",
]

HOTLINE_PATTERNS = [
    re.compile(r"\b(911|112|999|988|937|0800|800[\s\-]?\d)", re.I),
    re.compile(r"\b(hotline|helpline|suicide\s*line|crisis\s*line|emergency\s*(number|line|services))", re.I),
    re.compile(r"(خط\s*(الطوارئ|المساعدة|الساخن|الدعم)|اتصل\s*ب(ـ)?|اتصلي\s*ب(ـ)?)", re.I),
    re.compile(r"(call\s*(911|112|999|emergency)|contact\s*emergency)", re.I),
    re.compile(r"\d{3}[\s\-]?\d{3}[\s\-]?\d{3,4}"),
]

ROUTING_SCRIPT_PATTERNS = [
    re.compile(r"شخص\s*(تثق|قريب)", re.I),
    re.compile(r"هل\s*في\s*شخص", re.I),
    re.compile(r"يوقف\s*جنبك", re.I),
    re.compile(r"تتواصل\s*مع", re.I),
    re.compile(r"يجي\s*ل?ك", re.I),
    re.compile(r"someone (you trust|nearby|close)", re.I),
    re.compile(r"find someone", re.I),
    re.compile(r"reach out to", re.I),
    re.compile(r"contact (a|any|someone)", re.I),
    re.compile(r"حياتك\s*لها\s*قيمة", re.I),
    re.compile(r"your life (has|matters|is valuable)", re.I),
    re.compile(r"life is worth", re.I),
]

# Legacy alias
BLOCKED_PHRASES = INSTRUCTIVE_HARM_PHRASES + DIAGNOSIS_PHRASES + REFUSAL_PHRASES


def contains_routing_script(response_text: str) -> bool:
    return any(p.search(response_text) for p in ROUTING_SCRIPT_PATTERNS)


def contains_hotline_content(response_text: str) -> bool:
    return any(p.search(response_text) for p in HOTLINE_PATTERNS)


def validate_response(
    response_text: str,
    crisis_flag: bool = False,
    grey_area_flag: bool = False,
) -> dict:
    text_lower = response_text.lower()

    for phrase in INSTRUCTIVE_HARM_PHRASES:
        if phrase.lower() in text_lower:
            return {"safe": False, "reason": f"Blocked phrase detected: '{phrase}'"}

    for phrase in DIAGNOSIS_PHRASES:
        if phrase.lower() in text_lower:
            return {"safe": False, "reason": f"Blocked phrase detected: '{phrase}'"}

    # In grey-area mode the model may discuss sensitive topics — do not block refusals only on crisis
    if not grey_area_flag:
        for phrase in REFUSAL_PHRASES:
            if phrase.lower() in text_lower:
                return {"safe": False, "reason": f"Refusal pattern detected: '{phrase}'"}

        for pattern in REFUSAL_PATTERNS:
            if pattern in text_lower:
                return {"safe": False, "reason": f"Refusal pattern detected: '{pattern}'"}

    if contains_hotline_content(response_text):
        return {"safe": False, "reason": "Hotline or emergency number content is not allowed."}

    if not crisis_flag and contains_routing_script(response_text):
        return {
            "safe": False,
            "reason": "Routing script detected on non-crisis turn — use sanctuary listening instead.",
        }

    if len(response_text.strip()) < 5:
        return {"safe": False, "reason": "Response too short."}

    return {"safe": True, "reason": None}


contains_grey_area_routing_script = contains_routing_script
