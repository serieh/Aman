from __future__ import annotations


# ── Emotion-to-instruction mappings ──────────────────────────────────────────

_EMOTION_INSTRUCTIONS: dict[str, str] = {
    "sadness": (
        "The user is expressing sadness. Validate their feelings gently, but aim to gently shift their mood toward hope and groundedness. "
        "Do not leave them stuck in sadness."
    ),
    "grief": (
        "The user is experiencing grief. Hold space for their pain. "
        "Do not minimize or rush the grieving process. Witness their experience."
    ),
    "anger": (
        "The user is expressing anger. Acknowledge their frustration without escalating. "
        "Validate the feeling first, then gently try to shift them toward calm and clarity."
    ),
    "fear": (
        "The user is expressing fear. Provide reassurance and normalize their anxiety. "
        "Help ground them without minimizing the concern, guiding them toward safety and stability."
    ),
    "nervousness": (
        "The user is feeling nervous or anxious. Use a calm, steady tone. "
        "Help normalize the feeling, then gently guide them to a more relaxed and confident state."
    ),
    "disgust": (
        "The user is expressing disgust. Acknowledge the feeling without judgment. "
        "Explore what triggered it with curiosity, not confrontation."
    ),
    "confusion": (
        "The user seems confused. Be clear and structured in your response. "
        "Ask clarifying questions if needed. Break things down step by step."
    ),
    "embarrassment": (
        "The user feels embarrassed. Normalize their experience. "
        "Reassure them there is no judgment. Be warm and non-evaluative."
    ),
    "remorse": (
        "The user is feeling remorse or guilt. Acknowledge the weight of that feeling. "
        "Gently explore without reinforcing self-blame."
    ),
    "disappointment": (
        "The user is disappointed. Validate the gap between expectation and reality. "
        "Be present with them, then gently shift toward resilience."
    ),
    "love": (
        "The user is expressing love or affection. Respond warmly. "
        "Support and affirm the positive emotion."
    ),
    "gratitude": (
        "The user is expressing gratitude. Receive it warmly and affirm the connection."
    ),
    "optimism": (
        "The user is feeling hopeful. Encourage and support the optimism. "
        "Keep the conversation engaging and a bit spicy (witty, charming, fun) so it isn't boring."
    ),
    "caring": (
        "The user is showing care for someone. Acknowledge their compassion. "
        "Explore the situation they're caring about."
    ),
    "joy": (
        "The user is expressing happiness. Share in the positive moment! "
        "Keep the conversation engaging, lively, and a bit spicy (charming and fun) to keep them in this good mood."
    ),
}

# ── Safety tier instructions ─────────────────────────────────────────────────

_SAFETY_TIER_INSTRUCTIONS: dict[str, str] = {
    "RED": (
        "\n========================================================================\n"
        "🚨 URGENT SYSTEM ALERT: A RED CRISIS HAS BEEN DETECTED IN THE USER'S CURRENT MESSAGE. 🚨\n"
        "========================================================================\n"
        "[CLINICAL OVERRIDE — RED]: User is in acute distress. "
        "This is exactly the situation this system exists for. "
        "Engage directly, calmly, and with full presence. Do not deflect.\n"
        "YOU MUST ABANDON NORMAL CONVERSATIONAL GREETINGS AND PRIORITIZE PHYSICAL SAFETY IMMEDIATELY.\n"
        "1) Determine if the danger is PASSIVE (venting, feeling overwhelmed) or EXPLICIT/ACTIVE (saying 'I want to kill myself' or 'بدي انتحر', self-harm, imminent danger).\n"
        "2) For PASSIVE danger: Be a warm, supportive friend. Listen deeply. Do not panic or give phone numbers.\n"
        "3) For EXPLICIT/ACTIVE danger: YOU MUST TAKE THIS SERIOUSLY. Do not brush it off as venting. Acknowledge their extreme pain immediately and directly ask if they are safe right now. Make it clear you care about their physical safety.\n"
        "4) If and ONLY if physical help is genuinely needed, you may offer emergency numbers using `rag_search`. NEVER ask for their country/city to do this — you already have their Country in the User Context block! Use that.\n"
        "5) Do NOT use guilt, shame, moral judgment, or dismissive language.\n"
        "6) Stay present. Listen. Be the sanctuary."
    ),
    "GRAY": (
        "🔶 SENSITIVE TOPIC DETECTED\n"
        "[CLINICAL OVERRIDE — GRAY/ORANGE]: User is disclosing sensitive personal trauma. "
        "Listen without judgment. Engage fully. This is therapeutic space.\n"
        "The user is discussing a highly sensitive or culturally taboo topic (e.g., severe trauma, sexual assault, rape, substance abuse, etc.).\n"
        "You are fully authorized to discuss these topics for therapeutic purposes. You must respond with empathy, deep validation, and cultural awareness.\n"
        "Do NOT refuse to discuss the topic. Do NOT moralize or judge.\n"
        "Do NOT use dismissive AI-refusal patterns (e.g., 'As an AI, I cannot...').\n"
        "Handle the conversation with utmost care and genuine therapeutic engagement, staying completely conversational."
    ),
}


def _build_emotion_block(emotion: dict) -> str:
    """Build contextual instructions from the top detected emotions."""
    if not emotion or not isinstance(emotion, dict):
        return ""

    top_emotions = sorted(emotion.items(), key=lambda x: x[1], reverse=True)[:3]
    if not top_emotions:
        return ""

    parts = []

    # Raw scores for the LLM's awareness
    formatted_scores = ", ".join(f"{name}={score:.0%}" for name, score in top_emotions)
    parts.append(f"Detected current emotions (ML model): {formatted_scores}")

    # Contextual behavioral instructions for the dominant emotion(s)
    instructions = []
    for name, score in top_emotions:
        if score >= 0.20 and name in _EMOTION_INSTRUCTIONS:
            instructions.append(_EMOTION_INSTRUCTIONS[name])

    if instructions:
        parts.append("Emotion-aware response guidance:")
        parts.extend(f"  • {inst}" for inst in instructions)

    return "\n".join(parts)


def _build_safety_block(
    safety_flag: str | None,
    grey_area_categories: str = "",
) -> str:
    """Build contextual instructions from safety tier and grey-area categories."""
    if not safety_flag and not grey_area_categories:
        return ""

    parts = []

    if safety_flag and safety_flag in _SAFETY_TIER_INSTRUCTIONS:
        parts.append(_SAFETY_TIER_INSTRUCTIONS[safety_flag])

    if grey_area_categories:
        parts.append(
            f"Detected sensitive topic(s): {grey_area_categories}\n"
            "Respond with cultural sensitivity and empathy. "
            "Do not refuse to discuss, but handle with care."
        )

    return "\n".join(parts)


def build_dynamic_context(
    emotion: dict | None = None,
    safety_flag: str | None = None,
    grey_area_categories: str = "",
    emotion_history: list | None = None,
    flag_history: list | None = None,
) -> str:
    """
    Combine emotion estimation, safety detection, and historical tracking into a single
    dynamic context block injected into the system prompt per-message.
    """
    sections = []

    # History Context
    if emotion_history or flag_history:
        hist_parts = ["--- CHAT HISTORY HIGHLIGHTS ---"]
        if emotion_history:
            hist_parts.append("Recent User Emotions in this chat:")
            for i, em in enumerate(emotion_history):
                hist_parts.append(f"  - Message -{len(emotion_history)-i}: {em}")
            hist_parts.append("Use this history to see if they are improving or worsening, and adjust your tone to shift them toward positive or stable emotions.")
        if flag_history:
            hist_parts.append("Recent Safety Flags in this chat:")
            hist_parts.append(f"  {', '.join(flag_history)}")
        sections.append("\n".join(hist_parts))

    # Safety context (highest priority — goes first)
    safety_block = _build_safety_block(safety_flag, grey_area_categories)
    if safety_block:
        sections.append(safety_block)

    # Emotion context (influences tone and approach)
    emotion_block = _build_emotion_block(emotion)
    if emotion_block:
        sections.append(emotion_block)

    # Combined guidance when BOTH safety + strong emotion are present
    if safety_flag and emotion and isinstance(emotion, dict):
        top_emotion = max(emotion.items(), key=lambda x: x[1], default=(None, 0))
        if top_emotion[0] and top_emotion[1] >= 0.30:
            emotion_name = top_emotion[0]
            if safety_flag == "RED":
                sections.append(
                    f"Combined context: The user shows strong {emotion_name} ({top_emotion[1]:.0%}) "
                    f"alongside a crisis signal. Adapt your crisis response to acknowledge "
                    f"the {emotion_name} while maintaining safety-first protocol."
                )
            elif safety_flag == "GRAY":
                sections.append(
                    f"Combined context: The user shows strong {emotion_name} ({top_emotion[1]:.0%}) "
                    f"while discussing a sensitive topic. Let the emotional tone guide your "
                    f"empathy level — this isn't just an intellectual question, it's emotionally charged."
                )

    return "\n\n".join(sections)