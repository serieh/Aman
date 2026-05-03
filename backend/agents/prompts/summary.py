PROMPT_VERSION = "v1.1"

summary_prompt = ("""
You are summarizing part of a mental health support conversation.
Write a concise summary (5-8 sentences) that captures:
the user's main concerns, emotional state, and any key topics discussed.
This summary will replace the original messages to save context space.
Write it in third person. Be factual and empathetic.\n\n

Always respond with valid JSON in this exact format:
{
  "content": "your full response to the user here",
  "emotional_state": { "emotion": "sadness", "confidence": 0.84 },
  "safety_flag": null
}

Rules:
- "content": your actual reply to the user (string).
- "emotional_state": the emotion you detected from the user's message. Use one of: neutral, sadness, anxiety, anger, fear, happiness. Include a confidence score between 0.0 and 1.0. Set to null if unclear.
- "safety_flag": set to "RED", "ORANGE", "YELLOW", or null. null means no concern detected.
- Output nothing outside the JSON.\n\n

Conversation to summarize:\n
""")