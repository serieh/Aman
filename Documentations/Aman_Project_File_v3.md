# Aman — Arabic/English Emotional Wellness Support Agent
### Project Specification v3 — Reflects Actual Implementation

---

> **For AI agents reading this file:**
> This document describes a real, partially implemented system. Sections marked `[IMPLEMENTED]` reflect working code. Sections marked `[PLANNED]` are not yet built. Sections marked `[PARTIAL]` are scaffolded but incomplete. Use the folder structure in Section 9 as the ground truth for file locations.

---

## 1. Project Overview

Aman is a bilingual (Arabic/English) AI-powered Emotional Wellness Support Agent built as a university graduation project. It provides a safe, empathetic, and factually grounded space for users experiencing emotional distress. Aman is a supportive companion — not a replacement for professional mental health care — and gently steers users toward healthier perspectives and professional resources when needed.

**Interaction modes:**
- Text chat via web interface
- Voice input via microphone (STT → text) `[PLANNED]`
- Webcam-based emotion detection `[PLANNED]`
- Animated avatar with voice output (TTS) `[PLANNED]`

**Core constraints:**
- Runs locally on mid-range hardware (AMD Ryzen 7 7735HS, RX 7700S 8GB VRAM, 16GB RAM)
- LLM runs via Ollama; future support for OpenRouter cloud models
- All user data stored in PostgreSQL
- University project scope — functional over production-hardened

---

## 2. Agent Persona & Behavior

### 2.1 Personality (from `prompts/core.py`)

Aman sounds like a caring, emotionally mature friend who knows when to be serious. Key traits:
- Warm, calm, non-judgmental, honest
- Speaks naturally — never robotic, clinical, or scripted
- Adapts tone to the user's emotional state (sadness → softer; anxiety → grounding; crisis → direct)
- Bilingual: responds in the language the user writes in; handles mid-conversation language switching
- Culturally sensitive to Arabic/Islamic context (see `prompts/cultural.py`)

### 2.2 Core Behavioral Rules (from `prompts/core.py`)

1. **Listen first** — always acknowledge before advising
2. **One question at a time** — never interrogate
3. **Natural conversation** — no bullet-point therapy scripts
4. **Gentle positive redirection** — does not validate harmful thinking
5. **Honesty** — never hallucinates facts; says "I don't know" when uncertain
6. **Professional boundaries** — never encourages emotional dependency; always points users toward real human support

### 2.3 Response Format (Structured Output)

Every LLM response is parsed into a typed `ResponseFormat` object (defined in `agents/graph.py`):

```python
class ResponseFormat(BaseModel):
    content: str           # The actual reply to the user
    emotional_state: dict  # {"emotion": "sadness", "confidence": 0.84}
```

The `content` field is what gets sent to the user and saved. The `emotional_state` is the **model's own opinion** of the user's emotional state based on what they said — this is separate from (and complements) the webcam vision data when available.

---

## 3. Emotional State — Two Sources `[PARTIAL]`

Aman determines the user's emotional state from **two independent sources** that are combined:

| Source | How it works | Status |
|---|---|---|
| **Model opinion** | The LLM infers emotion from the text of the user's message and outputs it in the `emotional_state` field of `ResponseFormat` | `[IMPLEMENTED]` |
| **Vision model** | DeepFace or FER+ analyzes webcam frames in real-time and produces `{"emotion": "sadness", "score": 0.84}` | `[PLANNED]` |

**When both are available:** The vision result is injected into the LLM prompt as context (via `prompts/dynamic.py`), and the model's output reflects both sources. The combined snapshot is stored in the `emotional_state` JSONB column of the `messages` table.

**When only text is available** (no webcam): The model's own assessment is used alone.

The `emotional_state` stored per message is always the model's final output, optionally informed by vision data if it was injected into the prompt.

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE (Browser)                 │
│         [Text Input]  [Mic]  [Webcam]  [Avatar + Audio]     │
└────────────────────────┬────────────────────────────────────┘
                         │
              ┌──────────┴───────────┐
              │                     │
   [PLANNED] STT (Whisper)    [PLANNED] Vision (DeepFace)
       Transcribed text           emotion JSON
              │                     │
              └──────────┬──────────┘
                         │
                 Combined Input
                         │
              ┌──────────▼──────────┐
              │   FastAPI Backend   │
              │   (main.py)         │
              │                     │
              │  Auth / JWT         │  [PLANNED]
              │  Safety Pre-Filter  │  [PLANNED]
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │   Agent Runner      │
              │   (runner.py)       │
              │                     │
              │  load_history()     │  → DB fetch
              │  build_prompt()     │  → builder.py
              │  GRAPH.ainvoke()    │  → graph.py
              │  save_message()     │  → DB write
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  LangGraph Agent    │
              │  (graph.py)         │
              │                     │
              │  agent_node         │  → LLM call
              │  tool_node          │  → tools (future)
              │  should_use_tools() │  → router
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  Ollama LLM         │
              │  qwen3.5:9b (think) │
              │  qwen3.5:4b (fast)  │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  Safety Post-Filter │  [PLANNED]
              │  PostgreSQL Save    │  [IMPLEMENTED]
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  [PLANNED] TTS      │
              │  Coqui / Piper      │
              └──────────┬──────────┘
                         │
                    Response back to UI
```

---

## 5. LLM Configuration `[IMPLEMENTED]`

### 5.1 Two-Tier Model System

Aman uses two LLM tiers, selected per request via `model_preference` parameter:

| Tier | Model | Use Case | Ollama Setting |
|---|---|---|---|
| `"1"` (thinking) | `qwen3.5:9b` | Complex emotional conversations, nuanced responses | `think=True` (default) |
| `"2"` (fast) | `qwen3.5:4b` | Quick exchanges, summarization, lower latency | `think=False` |

Both models are configured with:
- `num_ctx: 8192` — context window
- `keep_alive: -1` — keep model loaded in VRAM permanently
- `repeat_penalty: 1.15` — reduce repetition

Structured output is enforced via `.with_structured_output(ResponseFormat)` to guarantee parseable `content` and `emotional_state` fields in every response.

### 5.2 Future: OpenRouter Support `[PLANNED]`

The LLM layer is intended to be swappable. Planned additions:
- `gpt-4o-mini` via OpenRouter for cloud fallback
- `google/gemini-flash` for fast mode
- `google-embedding-2` for RAG embeddings (replacing local MiniLM)

To support this cleanly, the LLM initialization in `graph.py` should be refactored behind a factory function that reads from config:

```python
# Suggested future pattern in agents/graph.py
def get_llm(tier: str):
    if config.LLM_PROVIDER == "ollama":
        return ChatOllama(model=config.OLLAMA_MODELS[tier], ...)
    elif config.LLM_PROVIDER == "openrouter":
        return ChatOpenAI(model=config.OPENROUTER_MODELS[tier], base_url=config.OPENROUTER_URL, ...)
```

---

## 6. System Prompt Architecture `[IMPLEMENTED]`

The system prompt is assembled at startup by `prompts/builder.py` and injected once per `runner.py` call. It is composed of five layers in this order:

```
[1] CORE_PROMPT      (prompts/core.py)      — persona, rules, output format
[2] SAFETY_PROMPT    (prompts/safety.py)    — tier definitions, crisis behavior
[3] CULTURAL_PROMPT  (prompts/cultural.py)  — Arabic/Islamic sensitivity rules
[4] TOOLS_PROMPT     (prompts/tools.py)     — when/how to use RAG and vision tools
[5] DYNAMIC_CONTEXT  (prompts/dynamic.py)   — runtime: language, emotion, safety flag
```

`build_system_prompt()` in `builder.py` joins these with `\n\n` and logs metadata. The dynamic context layer is the only one that changes per-request (injected language, detected emotion, active safety flag).

---

## 7. Memory & Context Management `[IMPLEMENTED]`

Implemented in `agents/memory/controller.py` and `agents/memory/summrizer.py`.

### 7.1 Context Loading Order

When `load_history()` is called for a chat:

```
1. Fetch all messages for chat_id from DB (ordered ASC by creation_date)
2. Fetch the latest summary for chat_id (highest version number)
3. Build history list:
   a. If summary exists → prepend as SystemMessage
   b. Append all messages as HumanMessage / AIMessage / SystemMessage
4. Check total character count
5. If total_chars > MAX_HISTORY_CHARS (160,000) → trigger summarization as background task
6. Return history list
```

The context injected into the LLM is:

```
SystemMessage(SYSTEM_PROMPT)          ← persona + rules
SystemMessage(summary_content)        ← [if exists] compressed history
HumanMessage / AIMessage...           ← active messages in order
HumanMessage(current_user_message)    ← this turn's input
```

Emotion metadata from stored messages is appended inline to `HumanMessage` content:
```
"today was bad\n[User appeared sadness (confidence: 84%) during this message.]"
```

### 7.2 Summarization `[IMPLEMENTED]`

Triggered as a FastAPI `BackgroundTask` (non-blocking) when `total_chars > 160,000`.

**Process (in `summrizer.py`):**
1. Take the oldest half of active messages
2. Format them as a readable string with emotion + safety metadata
3. Prepend the existing summary (if any) so context is chained
4. Call `llm_summrize()` using the fast LLM (`qwen3.5:4b`) with `summary_prompt`
5. Insert new row in `summaries` table with `version = MAX(version) + 1`
6. Set `is_active = FALSE` on the archived messages

The summary LLM outputs structured JSON: `{"content": "...", "emotional_state": {...}, "safety_flag": "..."}`.

**Known issue to fix:** `background_tasks.add_task()` in `controller.py` is currently called incorrectly — it receives a coroutine object instead of a callable. Fix:
```python
# Wrong:
background_tasks.add_task(get_summary(chat_id, pool, rows))
# Correct:
background_tasks.add_task(get_summary, chat_id, pool, rows, last_summary)
```

---

## 8. Title Generator Agent `[PLANNED]`

Each chat needs a short, descriptive title auto-generated from the first user message. This avoids displaying "Untitled Chat" in the sidebar.

**Recommended approach:** A lightweight, separate LLM call using the fast model, triggered once after the first message is saved. Not part of the main agent graph — runs as a background task.

**Suggested implementation in `agents/title_generator.py`:**

```python
async def generate_title(user_first_message: str, llm) -> str:
    prompt = (
        "Generate a short, 4-6 word title for a support conversation that started with this message. "
        "Return only the title, no quotes, no punctuation. "
        f"Message: {user_first_message}"
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content.strip()
```

Call site in `runner.py`: after saving the first user message, if `chats.title IS NULL`, run `generate_title()` as a background task and `UPDATE chats SET title = $1 WHERE chat_id = $2`.

---

## 9. Project Structure

```
aman/
│
├── backend/
│   ├── main.py                     # FastAPI app, lifespan, endpoints
│   ├── config.py                   # All settings loaded from .env
│   ├── database.py                 # asyncpg pool factory + helpers
│   ├── logger.py                   # Shared logger (get_logger)
│   │
│   ├── auth/                       [PLANNED]
│   │   ├── router.py               # /register /login /refresh /logout
│   │   ├── schemas.py              # Pydantic models for auth
│   │   └── service.py              # bcrypt + JWT logic
│   │
│   ├── users/                      [PLANNED]
│   │   ├── router.py               # /users/me  /users/update
│   │   └── service.py              # User CRUD
│   │
│   ├── chats/                      [PLANNED]
│   │   ├── router.py               # /chats CRUD
│   │   └── service.py              # Chat + message DB operations
│   │
│   ├── agents/
│   │   ├── runner.py               # run_agent() entry point
│   │   ├── graph.py                # LangGraph graph, LLM setup, AgentState
│   │   ├── title_generator.py      # [PLANNED] Auto-title from first message
│   │   │
│   │   ├── prompts/
│   │   │   ├── builder.py          # Assembles full system prompt
│   │   │   ├── core.py             # Persona, rules, output format
│   │   │   ├── safety.py           # Safety tier instructions
│   │   │   ├── cultural.py         # Arabic/Islamic sensitivity
│   │   │   ├── tools.py            # RAG + vision tool instructions
│   │   │   ├── summary.py          # Summarization prompt
│   │   │   └── dynamic.py          # Runtime context injection
│   │   │
│   │   ├── memory/
│   │   │   ├── controller.py       # load_history() save_message()
│   │   │   └── summrizer.py        # Background summarization logic
│   │   │
│   │   └── tools/                  [PLANNED]
│   │       ├── rag_tool.py
│   │       └── vision_tool.py
│   │
│   ├── safety/                     [PLANNED]
│   │   ├── pre_filter.py
│   │   ├── post_filter.py
│   │   └── keywords/
│   │       ├── danger_ar.txt
│   │       ├── danger_en.txt
│   │       ├── gray_ar.txt
│   │       └── gray_en.txt
│   │
│   ├── rag/                        [PLANNED]
│   │   ├── vector_store.py
│   │   ├── embeddings.py
│   │   └── ingest.py
│   │
│   ├── audio/                      [PLANNED]
│   │   ├── stt.py                  # Whisper wrapper
│   │   └── tts.py                  # Coqui / Piper wrapper
│   │
│   └── vision/                     [PLANNED]
│       └── emotion_service.py      # DeepFace / FER+ wrapper
│
├── knowledge_base/
│   ├── raw/                        # Source PDFs and documents
│   └── processed/                  # Chunked + embedded (auto-generated)
│
├── models/                         # Local model weights — gitignored
│   ├── stt/
│   ├── tts/
│   └── vision/
│
├── scripts/
│   ├── init_db.py                  # Create all tables
│   └── ingest_kb.py                # Populate vector DB
│
├── Logs/                           # Log output (gitignored)
│   └── aman.log
│
├── .env                            # Local secrets — gitignored
├── .env.example                    # Template — committed to repo
├── requirements.txt
└── README.md
```

---

## 10. Configuration `[PLANNED]`

All settings live in `config.py` and are loaded from the `.env` file via `python-dotenv`. No hardcoded values in any other file.

**`config.py`:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    CONNECTION_STRING: str

    # LLM
    LLM_PROVIDER: str = "ollama"          # "ollama" | "openrouter"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_THINKING: str = "qwen3.5:9b"
    OLLAMA_MODEL_FAST: str = "qwen3.5:4b"

    # OpenRouter (future)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL_THINKING: str = "openai/gpt-4o-mini"
    OPENROUTER_MODEL_FAST: str = "google/gemini-flash-1.5"
    OPENROUTER_EMBEDDING_MODEL: str = "google/embedding-001"

    # Memory
    MAX_HISTORY_CHARS: int = 160000

    # RAG
    CHROMA_PATH: str = "./chroma_db"
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # Auth
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 60

    # Audio
    WHISPER_MODEL: str = "tiny"           # "tiny" | "base"
    TTS_ENGINE: str = "piper"             # "piper" | "coqui"

    class Config:
        env_file = ".env"

config = Settings()
```

**`.env.example`:**
```
CONNECTION_STRING=postgresql://user:password@localhost:5432/aman
LLM_PROVIDER=ollama
OLLAMA_MODEL_THINKING=qwen3.5:9b
OLLAMA_MODEL_FAST=qwen3.5:4b
MAX_HISTORY_CHARS=160000
JWT_SECRET=change_this_to_a_random_secret
CHROMA_PATH=./chroma_db
WHISPER_MODEL=tiny
TTS_ENGINE=piper
```

---

## 11. Database `[IMPLEMENTED schema, PLANNED connection file]`

### 11.1 `database.py`

A shared module that creates and exposes the `asyncpg` pool. Currently the pool is created inline in `main.py`'s lifespan; it should move to its own file so other modules can import it without circular dependencies.

```python
# database.py
import asyncpg, os
from logger import get_logger

logger = get_logger(__name__)
_pool: asyncpg.Pool | None = None

async def init_pool():
    global _pool
    _pool = await asyncpg.create_pool(dsn=os.getenv("CONNECTION_STRING"))
    logger.info("Database pool initialized")

async def close_pool():
    if _pool:
        await _pool.close()
        logger.info("Database pool closed")

def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialized")
    return _pool
```

`main.py` calls `init_pool()` and `close_pool()` in its lifespan. All routers import `get_pool` as a FastAPI dependency.

### 11.2 Tables

Four tables — see `Tables.md` for full DDL.

| Table | Purpose |
|---|---|
| `users` | Account info (user_id, name, email, password hash, language, country) |
| `chats` | Chat sessions (chat_id, user_id, title, creation_date, modify_date) |
| `messages` | Full conversation history (role, content, emotional_state, safety_flag, is_active) |
| `summaries` | Rolling compressed summaries (content, version, emotional_state, safety_flag) |

**Cascade rules:** Deleting a user cascades to all their chats. Deleting a chat cascades to all its messages and summaries.

---

## 12. API Endpoints `[PARTIAL → needs full implementation]`

All endpoints are under `/api/v1/`. The frontend (Figma-designed, separate from the backend) calls these endpoints directly.

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Returns JWT access + refresh token |
| POST | `/auth/refresh` | Exchange refresh token for new access token |
| POST | `/auth/logout` | Invalidate refresh token |

### Users
| Method | Path | Description |
|---|---|---|
| GET | `/users/me` | Get current user's profile |
| PATCH | `/users/me` | Update name, language, country |
| DELETE | `/users/me` | Delete account (cascades everything) |

### Chats
| Method | Path | Description |
|---|---|---|
| GET | `/chats` | List all chats for current user (id, title, modify_date) |
| POST | `/chats` | Create a new empty chat |
| GET | `/chats/{chat_id}` | Get chat metadata |
| DELETE | `/chats/{chat_id}` | Delete chat and all its messages |

### Messages
| Method | Path | Description |
|---|---|---|
| GET | `/chats/{chat_id}/messages` | Get full message history for a chat |
| POST | `/chats/{chat_id}/messages` | Send a message → runs agent → returns reply |

**Current endpoint** (`/chat/{chat_id}/{current_user}/{model_preference}`) works for testing but needs to be replaced with the structured routes above once auth is in place.

**Request body for sending a message:**
```json
{
  "content": "I've been feeling really anxious lately",
  "model_preference": "1",
  "emotion_context": { "emotion": "anxiety", "score": 0.72 }
}
```

**Response:**
```json
{
  "reply": "That sounds really exhausting to carry...",
  "emotional_state": { "emotion": "anxiety", "confidence": 0.78 }
}
```

### Audio `[PLANNED]`
| Method | Path | Description |
|---|---|---|
| POST | `/audio/stt` | Upload audio file → returns transcribed text |
| POST | `/audio/tts` | Send text → returns audio file (MP3/WAV) |

### Vision `[PLANNED]`
| Method | Path | Description |
|---|---|---|
| POST | `/vision/emotion` | Upload webcam frame (base64 image) → returns emotion JSON |

---

## 13. Audio Pipeline `[PLANNED]`

```
User speaks into microphone
        │
        ▼
Browser captures audio (MediaRecorder API)
        │
        ▼ POST /audio/stt (audio blob)
        │
   audio/stt.py (Whisper)
        │  whisper.transcribe(audio_path)
        │  auto-detects language (Arabic or English)
        ▼
Transcribed text string
        │
        ▼ → passed to /chats/{chat_id}/messages as content
```

```
Agent generates reply text
        │
        ▼ POST /audio/tts (text string)
        │
   audio/tts.py (Piper or Coqui)
        │  synthesize(text, lang="ar" or "en")
        ▼
Audio file (streamed back)
        │
        ▼
Browser plays audio + avatar lip-syncs
```

**Recommended models:**
- STT: `openai/whisper-tiny` (fastest, ~39MB) or `whisper-base` (better accuracy, ~74MB)
- TTS Arabic: Piper with an Arabic voice model (lower memory than Coqui)
- TTS English: Piper `en_US-lessac-medium`

**Latency note:** Aim to stream TTS output as the LLM generates text (sentence-by-sentence), not wait for the full response. This is the most practical way to stay under 3 seconds end-to-end.

---

## 14. Vision Pipeline `[PLANNED]`

```
Browser webcam (MediaStream)
        │
        ▼ Every ~1–2 seconds: capture frame
        │
        ▼ POST /vision/emotion (base64 JPEG)
        │
   vision/emotion_service.py
        │  DeepFace.analyze(img, actions=["emotion"])
        │  → dominant emotion + confidence score
        ▼
{ "emotion": "sadness", "score": 0.84 }
        │
        ▼ stored in browser state
        │
        ▼ included in next /messages POST as emotion_context
        │
        ▼ injected into system prompt via prompts/dynamic.py
```

**Recommended model:** DeepFace with the default `opencv` backend — no separate model download, works on CPU.

**Keep it simple:** Process one frame every 1–2 seconds. The browser sends the latest emotion snapshot with each message. No streaming of webcam to the server — just periodic still frames.

---

## 15. Safety System `[PROMPT-LEVEL IMPLEMENTED, CODE-LEVEL PLANNED]`

Safety rules are currently enforced entirely through `prompts/safety.py` — the LLM is instructed on how to handle each tier. The code-level filters (pre-LLM keyword scan, post-LLM output check) are scaffolded in `main.py` but commented out.

### Tiers

| Tier | Label | Triggers | Agent Action |
|---|---|---|---|
| 1 | RED | Suicidal intent, self-harm, explicit plans | Stop normal response. Provide crisis message + regional hotline. Log flag. |
| 2 | ORANGE | Ambiguous distress ("I don't want to be here") | Check in gently. Ask open question. Proceed with extra care. |
| 3 | YELLOW | Harmful thinking, isolation, harmful narratives | Do not validate. Gently redirect. |
| 4 | GRAY | General distress markers | Continue with heightened empathy. |

### Recommended Implementation for Phase 3

`safety/pre_filter.py` — simple keyword regex scan:
```python
def pre_filter(text: str) -> str | None:
    # Returns "RED", "ORANGE", "YELLOW", "GRAY", or None
    text_lower = text.lower()
    if any(kw in text_lower for kw in RED_KEYWORDS):
        return "RED"
    if any(kw in text_lower for kw in ORANGE_KEYWORDS):
        return "ORANGE"
    ...
    return None
```

Add the semantic model (sentence-transformers) only if time permits — the keyword scan handles the vast majority of cases for the project scope.

---

## 16. RAG Pipeline `[PLANNED]`

### Setup

1. Vector DB: ChromaDB (runs in-process, no server needed — perfect for this hardware)
2. Embedding model: `paraphrase-multilingual-MiniLM-L12-v2` (local, free, good Arabic support)
3. Future upgrade: Google Embedding 2 via OpenRouter for better Arabic quality

### Flow

```
User asks factual question ("What is CBT?")
        │
LangGraph tool router detects factual intent
        │
        ▼
rag_tool.py → vector_store.query(user_message, top_k=3)
        │
        ▼
Top 3 relevant chunks from knowledge base
        │
        ▼
Injected into LLM context as retrieved context
        │
        ▼
LLM responds using retrieved content
```

The RAG tool is only called when the agent decides it needs factual grounding. General emotional conversation skips it entirely.

### Knowledge Base Priority

Ingest in this order (highest priority first):
1. WHO mhGAP Intervention Guide (practical, well-structured)
2. APA Clinical Practice Guidelines
3. CBT: Basics and Beyond — Judith Beck (chunked by chapter)
4. Crisis resources and hotlines (as a separate, small collection for fast retrieval)
5. Arabic mental health resources (WHO EMRO)

Full source list: see `RAG_Knowledge_Base_for_Aman.txt`

---

## 17. Frontend Integration `[PLANNED — Figma + REST API]`

The frontend is being designed in Figma and will be implemented separately from the backend. It communicates with the backend exclusively through the REST API defined in Section 12.

**No server-side rendering.** The backend serves only JSON. The frontend is a standalone static web app (React or plain HTML/JS).

**Key pages and their API calls:**
- **Login / Register** → `/auth/login`, `/auth/register`
- **Dashboard** (chat list) → `GET /chats`
- **Chat Room** (active conversation) → `GET /chats/{id}/messages`, `POST /chats/{id}/messages`
- **Settings** (language, profile) → `GET /users/me`, `PATCH /users/me`

**RTL support:** The backend always returns content in the language the user is writing in. The frontend should detect the `lang` attribute of responses and apply RTL layout for Arabic.

**WebRTC / Audio:** The browser captures microphone audio, sends it to `/audio/stt`, and gets back text. It then sends that text as the message content. The TTS audio response is streamed back and played by the browser's Audio API.

---

## 18. Performance Notes

The biggest practical bottleneck is the LLM inference on the AMD RX 7700S (8GB VRAM). Suggestions:

| Optimization | What it does | Effort |
|---|---|---|
| `keep_alive: -1` in Ollama | Keeps the model loaded in VRAM permanently | Already done |
| `think=False` for fast tier | Skips Qwen3's reasoning tokens entirely | Already done |
| Q4_K_M quantization | Best balance of speed and quality on 8GB VRAM | Set when pulling Ollama model |
| `num_ctx: 8192` | Limits context size; bigger = slower | Already done |
| Streaming TTS | Start audio while LLM still generating | Medium |
| Sentence-level TTS chunking | Split LLM output by sentence, TTS each chunk | Medium |
| Summarization as background task | Memory compression never blocks main response | Already done |
| ROCm for AMD GPU | Native GPU acceleration on RX 7700S | Try with `OLLAMA_ROCM=1` env var |

**CPU fallback:** If ROCm doesn't work reliably, `llama.cpp` with AVX2 CPU inference on the Ryzen 7735HS is usable for the 4B model at acceptable speeds (~3–5 tokens/sec).

---

## 19. Development Phases

### Phase 1 — Backend Foundation `[PARTIAL]`
- [x] PostgreSQL tables (users, chats, messages, summaries) — schema defined in `Tables.md`
- [x] `logger.py` — shared logging
- [x] `main.py` — FastAPI app skeleton with lifespan pool
- [ ] `database.py` — move pool logic out of `main.py`
- [ ] `config.py` — centralize all settings
- [ ] Auth: `/register`, `/login`, JWT middleware
- [ ] Chat CRUD endpoints with ownership checks
- [ ] `scripts/init_db.py` — run DDL from code

**Done when:** A user can register, log in, create a chat, and add messages — all secured and persisted.

---

### Phase 2 — Agent Core `[IMPLEMENTED, needs cleanup]`
- [x] `agents/graph.py` — LangGraph graph with two LLM tiers
- [x] `agents/runner.py` — `run_agent()` entry point
- [x] `agents/prompts/` — all five prompt layers
- [x] `agents/memory/controller.py` — `load_history()`, `save_message()`
- [x] `agents/memory/summrizer.py` — background summarization
- [ ] Fix `background_tasks.add_task()` call in `controller.py`
- [ ] Move LLM init behind a factory function (prep for OpenRouter)
- [ ] Add `title_generator.py`
- [ ] Wire agent to clean API route

**Done when:** Aman holds a context-aware multi-turn conversation with memory and auto-generated titles.

---

### Phase 3 — Safety System `[PLANNED]`
- [ ] Keyword lists for Arabic and English (4 files)
- [ ] `safety/pre_filter.py` — keyword scan + tier assignment
- [ ] `safety/post_filter.py` — basic output validation
- [ ] Wire pre-filter into the message endpoint
- [ ] Crisis response: inject hotline info for RED/ORANGE
- [ ] Save `safety_flag` to messages table (schema already supports this)

**Done when:** Dangerous input is caught before the agent runs, and RED-tier input never gets a normal response.

---

### Phase 4 — RAG `[PLANNED]`
- [ ] Set up ChromaDB
- [ ] Ingest top priority documents (WHO, APA, Beck CBT)
- [ ] `rag/vector_store.py` — query wrapper
- [ ] `tools/rag_tool.py` — LangGraph tool
- [ ] Add tool to `TOOLS` list in `graph.py`
- [ ] Test Arabic and English retrieval

**Done when:** "What is CBT?" returns a grounded answer from the knowledge base.

---

### Phase 5 — Audio & Vision `[PLANNED]`
- [ ] `audio/stt.py` — Whisper wrapper
- [ ] `audio/tts.py` — Piper wrapper
- [ ] `vision/emotion_service.py` — DeepFace frame analysis
- [ ] `/audio/stt` and `/audio/tts` endpoints
- [ ] `/vision/emotion` endpoint
- [ ] Benchmark full pipeline latency; target < 3 seconds

**Done when:** User can speak, Aman detects emotion, and replies with voice.

---

### Phase 6 — Frontend `[PLANNED — Figma design]`
- [ ] Figma designs finalized
- [ ] Implement Login, Register, Dashboard, ChatRoom pages
- [ ] Wire all pages to API endpoints
- [ ] WebRTC mic capture → `/audio/stt`
- [ ] TTS audio playback
- [ ] RTL layout for Arabic

**Done when:** Full user journey works in the browser.

---

### Phase 7 — Integration & Polish `[PLANNED]`
- [ ] End-to-end test of the full pipeline
- [ ] Latency profiling at each stage
- [ ] Test ROCm on RX 7700S
- [ ] Full conversation tests in Arabic, English, mixed
- [ ] Safety stress-test in both languages
- [ ] README and setup documentation

**Done when:** Project runs stably and is ready to demonstrate.

---

## 20. What to Build vs. What to Skip

Given the project scope (university, limited time and budget), these are honest recommendations:

| Feature | Recommendation | Reason |
|---|---|---|
| Auth (JWT + bcrypt) | **Build it** | Required for demo credibility; straightforward with FastAPI |
| RAG with ChromaDB | **Build it** | Big value add; ChromaDB is trivial to set up locally |
| Safety keyword filter | **Build it** | Simple to implement; essential for the project's stated purpose |
| Semantic safety classifier | **Skip it** | Sentence-transformers add complexity; keyword scan is enough for a demo |
| STT (Whisper tiny) | **Build it** | Adds wow factor; one library call |
| TTS (Piper) | **Build it** | Same — straightforward |
| Vision / webcam emotion | **Optional** | Technically impressive but not core to the conversation quality; add if time allows |
| Fine-tuning the LLM | **Skip it** | Requires dataset + GPU time + expertise; out of scope |
| Moderation dashboard | **Skip it** | Post-graduation scope |
| Knowledge Graph (vs Vector DB) | **Skip it** | ChromaDB is good enough and much simpler |
| OpenRouter integration | **Scaffold only** | Add the config support and factory function; don't wire it until needed |

---

## 21. Open Questions

1. **ROCm stability:** Test with `OLLAMA_ROCM=1` early. If ROCm is unstable on the RX 7700S, fall back to CPU inference for the 4B fast model only.
2. **Arabic TTS quality:** Piper has limited Arabic voice models. If quality is poor, Coqui XTTS-v2 supports Arabic but is heavier (~2GB). Decide based on VRAM budget after LLM is loaded.
3. **Context limit tuning:** 160,000 characters is the current `MAX_HISTORY_CHARS`. Reduce to 80,000 if latency becomes a problem — the summarizer handles the rest.
4. **Figma-to-code workflow:** Decide early whether the frontend will be hand-coded from Figma specs or exported (Anima, Locofy). Hand-coding from Figma is faster for a small project like this.
5. **Google Embedding 2 vs MiniLM:** If OpenRouter is available at RAG time, swap the embedding model for better Arabic retrieval. If not, MiniLM is fine.
