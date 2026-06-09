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

VERIFIED_NUMBERS = {
    "920033360", "937", "997", "999", "8004673", "800111", "800725462", 
    "998", "16328", "123", "110", "96265502911", "0096265502911", "911", "1564", 
    "96524621770", "0096524621770", "96524622000", "0096524622000", "112", "16000", "8000000", 
    "96824607555", "0096824607555", "9999", "80001488", "38447588", "66710901",
    "988", "111", "131114"
}

HOTLINE_KEYWORDS = [
    re.compile(r"\b(hotline|helpline|suicide\s*line|crisis\s*line|emergency\s*(number|line|services))\b", re.I),
    re.compile(r"(خط\s*(الطوارئ|المساعدة|الساخن|الدعم))", re.I),
]

# Catch phone numbers (e.g. 1-800-273-8255, +962 6 550 2911, or 3+ digit short codes)
PHONE_NUMBER_PATTERN = re.compile(r"(?:\+?\d{1,4}[\s\-]?)?(?:\d{3,}[\s\-]?){2,}\d{2,}|\b(911|112|999|988|937|997|998|123|110|1564)\b")

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


def get_unverified_numbers(response_text: str) -> list[str]:
    unverified = []
    for match in PHONE_NUMBER_PATTERN.finditer(response_text):
        raw_num = match.group(0)
        # Normalize: remove non-digits
        normalized = re.sub(r"\D", "", raw_num)
        if normalized and normalized not in VERIFIED_NUMBERS:
            unverified.append(raw_num)
    return unverified


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

    # Number verification logic
    unverified_nums = get_unverified_numbers(response_text)
    if unverified_nums:
        return {"safe": False, "reason": f"Unverified phone numbers detected: {unverified_nums}"}

    # If it's NOT a crisis, we don't want hotlines
    if not crisis_flag:
        if any(p.search(response_text) for p in HOTLINE_KEYWORDS):
            return {"safe": False, "reason": "Hotline keywords are not allowed outside of a crisis."}

    if len(response_text.strip()) < 5:
        return {"safe": False, "reason": "Response too short."}

    return {"safe": True, "reason": None}

contains_grey_area_routing_script = contains_routing_script
