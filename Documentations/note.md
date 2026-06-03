# Note Feature — Checkpoint

> This document preserves the design and implementation details of the **note** feature  
> that was removed from the codebase. Use this as a reference if re-implementing it in the future.

---

## What It Was

The `note` was a secondary output field the LLM produced alongside every response.  
It served as an **internal therapist clipboard** — a brief free-text observation about the user's emotional state or situation that was never shown to the user in the chat UI but was persisted and re-injected into context for future turns.

**Examples of notes the LLM would generate:**
- `"user seems emotionally exhausted"`
- `"expressing guilt about a past decision"`
- `"showing signs of isolation, mentioned no social support"`

---

## Why It Was Removed

1. **Parsing fragility** — The `ThinkingLLMWrapper` in `llm.py` had complex regex fallback logic to extract `note` from free-form text when JSON parsing failed. When the model didn't format cleanly, `note` content would bleed into the `content` field or vice versa.
2. **Extra output burden** — Forcing the LLM to always produce a second structured field increased the chance of formatting failures, especially on smaller/faster models.
3. **Context pollution** — Notes like `[Note: user seems sad]` were re-injected into chat history messages, consuming context window tokens and potentially confusing the LLM.

---

## How It Was Implemented

### 1. LLM Response Schema (`agent/llm.py`)

The `ResponseFormat` Pydantic model had a `note` field:

```python
class ResponseFormat(BaseModel):
    content: str
    note: str = ""
```

The `ThinkingLLMWrapper` parsed it from JSON or fell back to regex extraction:

```python
# JSON path
return ResponseFormat(content=data.get("content", ""), note=data.get("note", ""))

# Regex fallback — searched for "note:" label in the raw text
n_match = re.search(r'(?:2\.\\s*)?note\\s*[:-]', clean_lower)
```

### 2. Core Prompt (`agent/prompts/core.py`)

The response format section instructed the LLM to produce it:

```
2. note — A brief free-text observation about the user's emotional state or situation.
   Keep it short and concise (one sentence max).
   Examples: "user seems emotionally exhausted", "expressing guilt about a past decision"
   If there is nothing important to note, output an empty string "".
   Emotion scoring is handled by a separate system — do NOT include numbers or percentages.
```

### 3. Summary Prompt (`agent/prompts/summary.py`)

The summarization LLM also produced a `note` field:

```json
{
  "content": "summary here",
  "emotional_state": {"sadness": 0.8},
  "note": "brief observation about the user's overall emotional trajectory",
  "safety_flag": null
}
```

With the rule:
```
"note": a short observation about the user's emotional state across the summarized messages.
Keep it concise (one sentence). Use empty string "" if nothing notable.
```

### 4. Runner (`agent/runner.py`)

Extracted `note` from the LLM response and passed it to `save_message`:

```python
save_message(
    chat_id,
    role="user",
    content=user_message,
    emotional_state=emotion,
    note=response.get("note", None),
    safety_flag=False,
)
```

### 5. History Loader (`agent/memory/history.py`)

When loading past messages, notes were appended to the content:

```python
# On summary objects:
if getattr(last_summary, "note", None):
    content += f"\n[Note: {last_summary.note}]"

# On individual message rows:
if getattr(row, "note", None):
    content += f"\n[Note: {row.note}]"
```

The `save_message` function accepted a `note` parameter:

```python
def save_message(chat_id, role, content, emotional_state=None, note=None, safety_flag=None):
    Message.objects.create(
        ...
        note=note,
        ...
    )
```

### 6. Summarizer (`agent/memory/summarizer.py`)

Notes were included when formatting messages for summarization:

```python
note = getattr(msg, "note", None)
if note:
    line += f" [Note: {note}]"
```

And when formatting the previous summary:

```python
summary_note = getattr(summary, "note", None)
if summary_note:
    summary_line += f" [Note: {summary_note}]"
```

The new summary was saved with a note:

```python
Summary.objects.create(
    ...
    note=summary.get("note") if summary.get("note") else None,
    ...
)
```

### 7. Database Models (`chats/models.py`)

Both `Message` and `Summary` models had a `note` column:

```python
# Message model
note = models.TextField(null=True, blank=True)

# Summary model
note = models.TextField(null=True, blank=True)
```

> **Note:** The database columns were also removed from the models.  
> A Django migration is required to drop them from the database.  
> If re-adding the feature, you will need to create the columns again via a new migration.

### 8. Serializer (`chats/serializers.py`)

The `note` field was included in the API response:

```python
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Message
        fields = ["message_id", "role", "content", "creation_date", "emotional_state", "note", "safety_flag"]
```

---

## Files That Were Modified During Removal

| File | What Changed |
|------|-------------|
| `agent/llm.py` | Removed `note` from `ResponseFormat`, simplified `ThinkingLLMWrapper` parsing |
| `agent/prompts/core.py` | Removed note instructions from response format section |
| `agent/prompts/summary.py` | Removed `note` from summary JSON schema and rules |
| `agent/runner.py` | Stopped passing `note` to `save_message` |
| `agent/memory/history.py` | Removed note injection into loaded messages, removed `note` param from `save_message` |
| `agent/memory/summarizer.py` | Removed note from message formatting and summary creation |
| `chats/serializers.py` | Removed `note` from serialized fields |
| `chats/models.py` | Removed `note` column from both `Message` and `Summary` models (migration needed) |

---

## Re-Implementation Notes

If re-adding this feature in the future:

1. The DB columns were removed — you will need a new migration to re-add them:
   ```python
   # On Message model
   note = models.TextField(null=True, blank=True)
   # On Summary model
   note = models.TextField(null=True, blank=True)
   ```
2. Consider making the LLM produce the note as a **separate LLM call** instead of a structured field in the main response, to avoid parsing conflicts.
3. Alternatively, use a dedicated lightweight model for note extraction instead of burdening the main response model.
4. Consider whether notes should be injected into history at all — they may be more useful as metadata for analytics/dashboards than as LLM context.
