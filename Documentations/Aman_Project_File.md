# Aman — Arabic/English Emotional Wellness Support Agent
### Project Specification v5 — Django Backend + URL Map

---

> **For AI agents reading this file:**
> This document describes a fully functioning, partially implemented bilingual emotional wellness system. Sections marked `[IMPLEMENTED]` reflect working code present in the repository. Sections marked `[PLANNED]` are designated future features. Use the folder structure in Section 9 as the absolute ground truth for physical file locations. Do not follow legacy hypothetical layout architectures.

---

## 1. Project Overview

Aman is a bilingual (Arabic/English) AI-powered Emotional Wellness Support Agent built as a university graduation project. It provides a safe, empathetic, and factually grounded space for users experiencing emotional distress. Aman is a supportive companion — not a replacement for professional mental health care — and gently steers users toward healthier perspectives and professional resources when needed.

**Interaction modes:**
- Text chat via web interface `[IMPLEMENTED]`
- Voice input via microphone (STT → text) `[PLANNED]`
- Webcam-based emotion detection `[PLANNED]`
- Animated avatar with voice output (TTS) `[PLANNED]`

**Core constraints:**
- Runs locally on mid-range hardware
- LLM runs via Ollama; future support for OpenRouter cloud models `[PLANNED]`
- All user data stored in PostgreSQL `[IMPLEMENTED]`
- University project scope — functional over production-hardened

---

## 2. Agent Persona & Behavior

### 2.1 Personality (from `backend/agent/prompts/core.py`) `[IMPLEMENTED]`

Aman sounds like a caring, emotionally mature friend who knows when to be serious. Key traits:
- Warm, calm, non-judgmental, honest
- Speaks naturally — never robotic, clinical, or scripted
- Adapts tone to the user's emotional state (sadness → softer; anxiety → grounding; crisis → direct)
- Bilingual: responds in the language the user writes in; handles mid-conversation language switching
- Culturally sensitive to Arabic/Islamic context (see `backend/agent/prompts/cultural.py`)

### 2.2 Core Behavioral Rules (from `backend/agent/prompts/core.py`) `[IMPLEMENTED]`

1. **Listen first** — always acknowledge before advising
2. **One question at a time** — never interrogate
3. **Natural conversation** — no bullet-point therapy scripts
4. **Gentle positive redirection** — does not validate harmful thinking
5. **Honesty** — never hallucinates facts; says "I don't know" when uncertain
6. **Professional boundaries** — never encourages emotional dependency; always points users toward real human support

### 2.3 Response Format (Structured Output) `[IMPLEMENTED]`

Every LLM response is parsed into a typed `ResponseFormat` object (defined in `backend/agent/llm.py`):

```python
class ResponseFormat(BaseModel):
    content: str           # The actual reply to the user
    emotional_state: dict  # {"emotion": "sadness", "confidence": 0.84}
```

The `content` field is what gets sent to the user and saved. The `emotional_state` is the **model's own opinion** of the user's emotional state based on what they said — separate from (and complementing) webcam vision data when available.

---

## 3. Emotional State — Two Sources `[PARTIAL]`

Aman determines the user's emotional state from **two independent sources**:

| Source | How it works | Status |
|---|---|---|
| **Model opinion** | The LLM infers emotion from the user's message text and outputs it in `ResponseFormat.emotional_state` | `[IMPLEMENTED]` |
| **Vision model** | DeepFace or FER+ analyzes webcam frames and produces `{"emotion": "sadness", "score": 0.84}` | `[PLANNED]` |

**When both are available:** The vision result is injected into the LLM prompt, and the model's output reflects both sources. The combined snapshot is stored in the `emotional_state` JSONB column of the `messages` table.

**When only text is available** (no webcam): The model's own assessment is used alone.

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
              │   Django Backend    │
              │   (ASGI / DRF API)  │
              │                     │
              │  Auth / JWT Tokens  │  [IMPLEMENTED]
              │  Safety Pre-Filter  │  [PLANNED]
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │   Agent Runner      │
              │   (agent/runner.py) │
              │                     │
              │  load_history()     │  → DB fetch (Django ORM)
              │  build_prompt()     │  → agent/prompts/builder.py
              │  GRAPH.invoke()     │  → agent/graph.py
              │  save_message()     │  → DB write (Django ORM)
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  LangGraph Agent    │
              │  (agent/graph.py)   │
              │                     │
              │  agent_node         │  → LLM call
              │  tool_node          │  → tools (planned)
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  Ollama LLM         │
              │  gemma4:31b (think) │
              │  gemma4:e2b (fast)  │
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

Aman uses two LLM tiers, selected per request via the `model` parameter in request payloads:

| Tier | Model | Use Case | Ollama Setting |
|---|---|---|---|
| `"1"` (thinking) | `gemma4:31b` | Complex emotional conversations, nuanced responses | `think=True` (default) |
| `"2"` (fast) | `gemma4:e2b` | Quick exchanges, summarization, lower latency | `think=False` |

Both models are configured with:
- `num_ctx: 8192` — context window
- `keep_alive: -1` — keep model loaded in VRAM permanently
- `repeat_penalty: 1.15` — reduce repetition

Structured output is enforced via `.with_structured_output(ResponseFormat)`.

---

## 6. System Prompt Architecture `[IMPLEMENTED]`

The system prompt is assembled at startup by `backend/agent/prompts/builder.py` and injected once per `runner.py` call. Five layers, joined in order:

```
[1] CORE_PROMPT      (backend/agent/prompts/core.py)      — persona, rules, output format
[2] SAFETY_PROMPT    (backend/agent/prompts/safety.py)    — tier definitions, crisis behavior
[3] CULTURAL_PROMPT  (backend/agent/prompts/cultural.py)  — Arabic/Islamic sensitivity rules
[4] TOOLS_PROMPT     (backend/agent/prompts/tools.py)     — when/how to use RAG and vision tools
[5] DYNAMIC_CONTEXT  (backend/agent/prompts/dynamic.py)   — runtime: language, emotion, safety flag
```

`build_system_prompt()` joins these with `\n\n`. The dynamic context layer is the only one that changes per-request.

---

## 7. Memory & Context Management `[IMPLEMENTED]`

Implemented in `backend/agent/memory/history.py` and `backend/agent/memory/summarizer.py`.

### 7.1 Context Loading Order

When `load_history()` is called for a chat session:
1. Fetch active messages for the `chat_id` from the database ordered by `creation_date`.
2. Fetch the latest `Summary` record (ordered descending by `version`).
3. Build the LangChain history sequence:
    * If a summary exists → prepend it to history as a `SystemMessage` with the summarized emotional context.
    * Append all active messages in chronological order as `HumanMessage` or `AIMessage`.
4. If the active message list length meets or exceeds `MAX_MESSAGES_BEFORE_SUMMARY` (default: 40):
    * Trigger a background thread (`threading.Thread`) running `run_summarization_background` to compress context without blocking the current request.
5. Return history list.

### 7.2 Summarization `[IMPLEMENTED]`

Triggered as an asynchronous background thread when message thresholds are met.

**Process (in `backend/agent/memory/summarizer.py`):**
1. Select the oldest 50% of the active messages.
2. Format them into a readable conversation script including their emotional snapshots and safety tags.
3. Prepend the existing summary (if any).
4. Invoke `llm_summarize()` using the fast LLM (`gemma4:e2b`) with `SUMMARY_PROMPT`.
5. Insert a new record in the `summaries` table, incrementing the version: `version = Max("version") + 1`.
6. Set `is_active = FALSE` on the summarized messages.

---

## 8. Title Generator Agent `[IMPLEMENTED]`

Each conversation is labeled with a short, descriptive title automatically generated from the first user message.

**Implementation in `backend/agent/llm.py`:**
```python
def title_generator(user_message: str):
    llm = ChatOllama(model=LLM_FAST_MODEL)
    messages = [
        SystemMessage(content=TITLE_PROMPT),
        HumanMessage(content=user_message)
    ]
    reply = llm.invoke(messages)
    return reply.content.strip()
```

**Execution Pipeline (in `backend/agent/runner.py`):**
If a chat has no messages yet and its title is `"Untitled Chat"`, the runner launches a background thread:
```python
threading.Thread(
    target=_generate_title_background,
    args=(user_message, chat_id),
    daemon=True,
).start()
```
The thread safely updates the chat record in the database using Django ORM and closes database connections on completion.

---

## 9. Physical Project Structure `[IMPLEMENTED]`

The verified physical directory layout of the application is flat and clean under `backend/`:

```
backend/
│
├── manage.py                           # Django command-line execution entry point
├── logger.py                           # Centralized system logger
├── Logs/                               # Runtime log outputs (gitignored)
│   └── aman.log
│
├── backend/                            # Django System Core
│   ├── settings.py                     # Root Django configurations
│   ├── urls.py                         # Root URL routing table
│   ├── asgi.py                         # ASGI asynchronous configuration
│   └── wsgi.py                         # WSGI synchronous fallback configuration
│
├── api/                                # App: Authentication Pages & REST APIs
│   ├── serializers.py                  # Register/Login schema validators
│   ├── urls.py                         # Auth URLs (/api/v1/auth/* and pages)
│   └── views.py                        # Registers, Logins, and Token blacklisting
│
├── users/                              # App: Profile management and user settings
│   ├── models.py                       # User Model (UUID primary key "id")
│   ├── serializers.py                  # Profile serialization
│   ├── urls.py                         # Profile routes (/settings/ and /api/v1/users/me/)
│   └── views.py                        # CRUD view logic for profiles
│
├── chats/                              # App: Core Domain (Dashboard, Chats, AI API)
│   ├── models.py                       # Chat, Message, and Summary models
│   ├── serializers.py                  # Message/Chat payload schemas
│   ├── urls.py                         # Chat routes (/dashboard/, chat rooms, API CRUD)
│   └── views.py                        # Views bridging Django REST and agent engine
│
└── agent/                              # Module: Independent LangGraph AI Engine
    ├── config.py                       # LLM variables and context settings
    ├── graph.py                        # LangGraph DAG compilation
    ├── llm.py                          # Ollama LLM model initializations
    ├── runner.py                       # Synchronous thread-safe entry point
    │
    ├── prompts/                        # System prompt layers
    │   ├── builder.py                  # Dynamic prompt assembly
    │   ├── core.py                     # Main agent rules and persona
    │   ├── safety.py                   # Safety handling rules
    │   ├── cultural.py                 # Islamic/Arabic guidelines
    │   ├── tools.py                    # RAG/Vision context instructions
    │   ├── summary.py                  # Summarization prompts
    │   ├── title.py                    # Title generation prompts
    │   └── dynamic.py                  # Prompt runtime context generator
    │
    ├── memory/                         # History compaction
    │   ├── history.py                  # DB history loader
    │   └── summarizer.py               # Rolling summaries compiler
    │
    └── tools/                          # Integrations (Planned RAG/Vision tools)
        └── __init__.py
```

---

## 10. Database Model Design `[IMPLEMENTED]`

### 10.1 User Model (`backend/users/models.py`)
```python
class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    birthdate = models.DateField()
    gender = models.CharField(max_length=10, choices=[("male", "male"), ("female", "female")])
    country = models.CharField(max_length=2) # ISO 3166-1 alpha-2 code
    creation_date = models.DateTimeField(auto_now_add=True)
```

### 10.2 Chat Model (`backend/chats/models.py`)
```python
class Chat(models.Model):
    chat_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="id")
    title = models.CharField(max_length=255, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)
```

### 10.3 Message Model (`backend/chats/models.py`)
```python
class Message(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, db_column="chat_id")
    role = models.CharField(max_length=20)
    content = models.TextField()
    creation_date = models.DateTimeField(auto_now_add=True)
    emotional_state = models.JSONField(null=True, blank=True)
    safety_flag = models.CharField(max_length=10, null=True, blank=True)
    is_active = models.BooleanField(default=True)
```

### 10.4 Summary Model (`backend/chats/models.py`)
```python
class Summary(models.Model):
    summary_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, db_column="chat_id", related_name="summaries")
    content = models.TextField()
    emotional_state = models.JSONField(blank=True, null=True)
    safety_flag = models.CharField(max_length=10, blank=True, null=True)
    version = models.IntegerField(default=1)
    creation_date = models.DateTimeField(auto_now_add=True)
```

---

## 11. Complete Endpoint Routing Matrix `[IMPLEMENTED]`

All routes mapped in Django apps are detailed in `URL_API_Mapping.md`.

*   **POST** `/api/v1/auth/register/` - Registration
*   **POST** `/api/v1/auth/login/` - Login
*   **POST** `/api/v1/auth/refresh/` - Refresh Token
*   **POST** `/api/v1/auth/logout/` - Invalidation
*   **GET/PUT/DELETE** `/api/v1/users/me/` - Profile management
*   **GET/POST** `/api/v1/chats/` - Chat list and instantiation
*   **GET/DELETE** `/api/v1/chats/<uuid:chat_id>/` - Retrieve conversation history or delete
*   **POST** `/api/v1/chats/<uuid:chat_id>/message/` - Send message and obtain agent response

---

## 12. Tech Stack Summary

- **Backend Web Framework**: Django + Django REST Framework (DRF)
- **Authentication**: JWT (JSON Web Tokens) via `djangorestframework-simplejwt`
- **Agent Orchestrator**: LangGraph + LangChain Core
- **LLM Engine**: Ollama (Running locally)
- **Database**: PostgreSQL (Access via Django ORM)
- **Logger**: Python Standard `logging` (custom configured in `backend/logger.py`)
- **Package Manager**: UV
