PROMPT_VERSION = "v1.3"

SUMMARY_PROMPT = ("""
You are summarizing part of a mental health support conversation.
Write a concise summary (5-8 sentences) that captures:
the user's main concerns, emotional state, and any key topics discussed.
This summary will replace the original messages to save context space.
Write it in third person. Be factual and empathetic.\n\n

Always respond with valid JSON in this exact format:
{
  "content": "your factual summary of the conversation here",
  "emotional_state": {"sadness": 0.8, "fear": 0.4},
  "safety_flag": null
}

Rules:
- "content": your factual summary of the conversation (string).
- "emotional_state": read the emotions provided for each message in the history. Select the most prevalent and strong emotions across the whole window and their scores. Output a JSON object mapping the top emotion labels to their average/prevalent scores (0.0 to 1.0).
- "safety_flag": set to "RED", "ORANGE", "YELLOW", or null. null means no concern detected.
- Output nothing outside the JSON.\n\n

Conversation to summarize:\n
""")