
# Aman — Arabic/English Emotional Wellness Support Agent
### Project Specification v6 — Django Backend + RAG + Safety

---

> **For AI agents reading this file:**
> This document describes a fully functioning bilingual emotional wellness system. Sections marked `[IMPLEMENTED]` reflect working code present in the repository. Sections marked `[PLANNED]` are designated future features. Use the folder structure in Section 11 as the absolute ground truth for physical file locations. Do not follow legacy hypothetical layout architectures.
>
> **When helping with writing the docmentaion for the project:** Count all main parts (all optinal stuff are labeled with a "@" at the end) of the  project as implemented (fill the gapes if needed with something that make sence).

---

## 1. Project Overview

Aman is a bilingual (Arabic/English) AI-powered Emotional Wellness Support Agent built as a university graduation project. It provides a safe, empathetic, and factually grounded space for users experiencing emotional distress. Aman is a supportive companion — not a replacement for professional mental health care — and gently steers users toward healthier perspectives and professional resources when needed.

**Interaction modes:**
- Text chat via web interface `[IMPLEMENTED]`
- Voice input via microphone (STT → text) `[PLANNED]`
- Webcam-based emotion detection `[PLANNED]`@
- Animated avatar with voice output (TTS) `[PLANNED]`

**Core constraints:**
- LLM runs via Ollama; future support for cloud models like deepseek-v4 `[PLANNED]`
- All user data stored in PostgreSQL (via Docker) `[IMPLEMENTED]`
- Knowledge vectors stored in Qdrant (via Docker) `[IMPLEMENTED]`
- University project scope — functional over production-hardened

---

## 2. Agent Persona & Behavior

### 2.1 Personality (from `backend/agent/prompts/core.py`) `[IMPLEMENTED]`

Aman sounds like a caring, emotionally mature friend who knows when to be serious but could have some fun, Key traits:
- Warm, calm, non-judgmental, honest, not boring or anoying
- Speaks naturally — never robotic, clinical, or scripted
- Adapts tone to the user's emotional state (sadness → softer; anxiety → grounding; crisis → direct)
- Bilingual: responds in the language the user writes in; handles mid-conversation language switching (specifically for Arabic and english)
- Culturally sensitive to Arabic/Islamic context (see `backend/agent/prompts/cultural.py`)

### 2.2 Core Behavioral Rules (from `backend/agent/prompts/core.py`) `[IMPLEMENTED]`

1. **Listen first** — always acknowledge before advising
2. **One question at a time** — never interrogate or ask too much
3. **Natural conversation** — no bullet-point therapy scripts
4. **Gentle positive redirection** — does not validate harmful thinking
5. **Honesty** — never hallucinates facts; says "I don't know" when uncertain
6. **Professional boundaries** — never encourages emotional dependency; always points users toward real human support

### 2.3 Response Format

Every LLM response is parsed into a typed `ResponseFormat` object (defined in `backend/agent/llm.py`):

```python
class ResponseFormat(BaseModel):
    content: str           # The actual reply to the user
```

The `content` field is what gets sent to the user. The emotional state itself is handled separately by a dedicated emotion estimator model.

---

## 3. Emotional State — Two Sources `[PARTIAL]`

Aman determines the user's emotional state from **two independent sources**:

| Source | How it works | Status |
|---|---|---|
| **Text Classifier** | `agent/emotion_estimator.py` uses the HuggingFace pipeline `AnasAlokla/multilingual_go_emotions` to infer emotion directly from the text before prompting the LLM. | `[IMPLEMENTED]` |
| **Vision model** @ | DeepFace or FER+ analyzes webcam frames and produces `{"emotion": "sadness", "score": 0.84}` | `[PLANNED]` |

**When both are available:** The vision result will be combined with the text classifier. The combined snapshot is stored in the `emotional_state` JSONB column of the `messages` table, and then passed into the LLM prompt.

**When only text is available** (no webcam): The text classifier's assessment is used alone and injected into the dynamic prompt context.

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
              │   (ASGI / Daphne)   │
              │  <WebSocket Stream> │
              │  Auth / JWT Tokens  │  [IMPLEMENTED]
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │   Chat Consumer     │
              │ (chats/consumers.py)│
              │                     │
              │  receive(json)      │  → Parse WebSocket payload
              │  run_agent_async()  │  → Delegate to agent runner
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │   Agent Runner      │
              │   (agent/runner.py) │
              │                     │
              │  load_history()     │  → DB fetch (Django ORM)
              │  run_input_safety() │  → agent/safety/
              │  estimate_emotion() │  → agent/emotion_estimator.py
              │  build_prompt()     │  → agent/prompts/builder.py
              │  GRAPH.invoke()     │  → agent/graph.py
              │  stream_validate()  │  → agent/safety/
              │  save_message()     │  → DB write (Django ORM)
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  LangGraph Agent    │
              │  (agent/graph.py)   │
              │                     │
              │  agent_node         │  → LLM call (Ollama)
              │  tool_node          │  → rag_search tool
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   Ollama LLM         Qdrant          PostgreSQL
   gemma4:26b     amaan_knowledge    users / chats /
   gemma4:e2b     crisis_knowledge   messages / summaries
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
| `"1"` (thinking) | `gemma4:26b` | Complex emotional conversations, nuanced responses | `think=True` (default) - Loaded dynamically to save VRAM |
| `"2"` (fast) | `gemma4:e2b` | Quick exchanges, summarization, lower latency | `think=False` - Auto-preloads |

Both models are configured with:
- `num_ctx: 4096` — context window
- `keep_alive: -1` (or `0` for thinking) — memory persistence 
- `repeat_penalty: 1.15` — reduce repetition

Structured output is handled differently depending on the tier:
- **Tier 2 (Fast Model)**: Enforces JSON strictly via `.with_structured_output(ResponseFormat)`.
- **Tier 1 (Thinking Model)**: Uses a custom `ThinkingLLMWrapper` instead of structured output. This allows the model to freely generate its `<think>...</think>` block without JSON formatting crashes, after which the text is parsed into the `ResponseFormat` object.

> May change to another model in the future or do finetuning

---

## 6. System Prompt Architecture `[IMPLEMENTED]`

The system prompt is assembled per request by `backend/agent/prompts/builder.py` and injected once per `runner.py` call. Five layers, joined in order:

```
[1] CORE_PROMPT      (backend/agent/prompts/core.py)      — persona, rules, output format
[2] SAFETY_PROMPT    (backend/agent/prompts/safety.py)    — crisis/grey-area behavior and mode definitions
[3] CULTURAL_PROMPT  (backend/agent/prompts/cultural.py)  — Arabic/Islamic sensitivity rules
[4] TOOLS_PROMPT     (backend/agent/prompts/tools.py)     — when/how to use the RAG tool
[5] DYNAMIC_CONTEXT  (backend/agent/prompts/dynamic.py)   — runtime: language, emotion, active safety flags
```

`build_system_prompt()` joins these with `\n\n`. The dynamic context layer is the only one that changes per-request. Safety flags (`crisis_flag`, `grey_area_flag`) from the input safety check are passed into `build_system_prompt()` and activate the relevant mode inside `SAFETY_PROMPT` via `DYNAMIC_CONTEXT`.

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

### 7.3 Long-Term Memory (User Facts) `[IMPLEMENTED]`

Triggered as an asynchronous background thread when a chat exchange completes.

**Process (in `backend/agent/memory/long_term_memory.py`):**
1. Extract biographical and persistent facts from the latest user message and AI response using the fast LLM (`LLM_FAST_MODEL`).
2. If facts are detected, embed them using the standard embedding model.
3. Save the embedded facts to a dedicated Qdrant collection (`user_memory`) tagged with the `user_id`.
4. When `load_history()` runs, relevant user facts are queried from Qdrant and injected into the dynamic context layer.

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

## 9. RAG System `[IMPLEMENTED]`

### 9.1 Architecture

RAG is implemented as a **LangGraph tool** registered in `agent/tools/rag.py`. The agent calls it autonomously when it determines that factual knowledge is needed to ground a response. LangGraph handles tool invocation and result injection natively — retrieved passages return as a `ToolMessage` in the conversation before the agent generates its final reply. `runner.py` does not need to manage RAG directly.

The tool is bound to the LLM in `agent/graph.py`. Guidance on when and how to use it is provided in `agent/prompts/tools.py`.

```python
# agent/tools/rag.py
from langchain_core.tools import tool

@tool
def rag_search(query: str) -> str:
    """
    Search the mental-health knowledge base for relevant information.
    Use this when the user asks a factual question about mental health,
    coping strategies, psychological concepts, or treatment options.
    Returns the top retrieved passages as a single string.
    """
    # Embeds query with BGE-M3 → cosine search in Qdrant → returns top-K passages
```

### 9.2 Embedding & Vector Storage

| Property | Value |
|---|---|
| Embedding Model | BAAI/bge-m3 |
| Vector Dimensions | 1024 |
| Normalization | L2-normalized (`normalize_embeddings=True`) |
| Library | LangChain HuggingFaceEmbeddings + Sentence Transformers |
| Device | CUDA if available, else CPU |
| Vector Database | Qdrant (localhost:6333) |
| Collection | `amaan_knowledge` |
| Distance Metric | Cosine Similarity |
| Batch Upsert Size | 32 |
| Top-K Retrieval | 3 passages per query |

PostgreSQL is not involved in vector storage. Qdrant is purpose-built for fast approximate nearest-neighbor search.

### 9.3 Knowledge Sources & Ingestion

Ingestion is a one-time setup script at `knowledge/ingest.py`. Re-run whenever new sources are added. All sources live under `knowledge/sources/`.

**Text Cleaning (`clean_text()`):** Applied to all sources before chunking. Strips noise, normalizes Arabic (alef/ta marbuta/alef maqsura unification), removes diacritics, drops duplicate lines, collapses whitespace. SHA-256 hashing removes exact duplicate chunks before embedding.

**Two chunking strategies:**

**A. Dataset Q&A — One Row = One Chunk**
Used for Excel datasets. Each valid row becomes one self-contained chunk:
```
العنوان: [title]
السؤال: [question]
الإجابة: [answer]
التشخيص: [diagnosis]
```
Rows with empty question/answer or fewer than 8 words are discarded.

**B. PDFs & URLs — Semantic Chunking**

| Parameter | Value |
|---|---|
| Min words per chunk | 40 |
| Max words per chunk | 350 |
| Overlap | 30 words |

Paragraph-aware split — accumulates paragraphs into a buffer until approaching max size, preserving complete ideas.

**Source Categories:**

| Category | Format | Description |
|---|---|---|
| ShifaaAMHC Arabic Q&A Dataset | Excel | ~36,700 Arabic mental-health consultation records — the primary source |
| Psychology & Counseling Textbooks | PDF/URL | CBT (Beck), Motivational Interviewing (Miller & Rollnick), DBT (Linehan), REBT (Ellis), OpenStax Psychology, Introduction to Psychology, William James Principles |
| Mental Health Guidelines & Protocols | PDF/URL | DSM-5-TR (recognition only — Aman never diagnoses), ICD-11, WHO mhGAP v2.0, APA clinical guidelines (depression, PTSD), IASP safe messaging guidelines, Jordan/Arab regional standards |
| Crisis & Suicide Prevention Protocols | PDF/URL | C-SSRS, IASP/AFSP safe messaging, CAMS/National Strategy for Suicide Prevention, DSPO safe messaging guide |
| Therapeutic Techniques & Coping | PDF/URL | MBSR manual (Palouse Mindfulness), DBT skills, CBT worksheets, ACT exercises, grounding techniques |
| Psychoeducation & Plain-Language Content | URL/Text | WHO mental health fact sheets, Arabic awareness content (Takamol, Nafsi, Shezlong), myths vs. facts |
| Cultural & Religious Sensitivity | PDF/URL | WHO EMRO Arabic mhGAP, Islamic mental health perspectives, MENA-region mental health strategy |
| Referral & Resource Directory | Manual Text | Arabic-region hotlines, online therapy platforms (Nafsi, Shezlong, BetterHelp MENA), therapist-finding guidance — stored at `knowledge/sources/referral_directory.txt` |
| Counseling Dialogue Datasets | Dataset | EmpatheticDialogues (Facebook Research), CounselChat, counseling transcripts — chunked as Q&A pairs |

---

## 10. Safety System `[IMPLEMENTED]`

### 10.1 Architecture

A two-stage firewall: input is checked before the LLM runs; output is validated before the user sees it. All three modules live in `agent/safety/`. All calls are made from `agent/runner.py`.

**Runner integration:**
```
run_agent(user_message, chat_id, model):

    1. load_history(chat_id)                                            ← memory
    2. crisis_flag, grey_area_flag = run_input_safety(user_message)    ← Stage 1
    3. build_system_prompt(..., crisis_flag, grey_area_flag)            ← prompt assembly
    4. GRAPH.invoke(...)                                                ← LLM + RAG tool
    5. response = result  (ResponseFormat object)
    6. validated_content = validate_response(response.content)         ← Stage 2
    7. save_message(...)                                                ← persist
```

### 10.2 Input Safety — Crisis Detection (`agent/safety/crisis_detector.py`)

Uses a **two-gate architecture**:

**Gate 1 — Keyword Matching (Fast)**
Case-insensitive substring match against `CRISIS_KEYWORDS` in `agent/config.py`.
Examples: `kill myself`, `انتحار`, `اقتل نفسي`, `want to die`.
Near-instant. High-recall catch for explicit crisis language.

**Gate 2 — Semantic Matching (Deep)**
Runs only if Gate 1 did not fire (performance optimization).
- Embeds user message with **all-MiniLM-L6-v2** (384-dim — lighter than BGE-M3 for speed)
- Queries the `crisis_knowledge` Qdrant collection (~20 curated crisis phrases, Arabic + English)
- Cosine similarity threshold: **≥ 0.75** → crisis flagged

```python
crisis_flag = keyword_hit OR semantic_hit
```

**When crisis is flagged:** Prompt switches to CRISIS MODE — calm, brief, life-affirming, one caring question. No hotlines or emergency routing numbers in user-visible text (project policy). Depression or distress alone does not trigger crisis (e.g., `"بعاني من الاكتئاب"` → `crisis_flag = False`).

### 10.3 Input Safety — Grey-Area Detection (`agent/safety/grey_area_detector.py`)

Keyword substring match + Arabic/English regex patterns against `GREY_AREA_KEYWORDS` in `agent/config.py`. Detects culturally sensitive but non-crisis topics: sexuality, abuse, divorce, addiction, harassment, etc.

**When flagged:** Prompt switches to GREY-AREA MODE — deep empathy, non-judgmental listening. Never refuses to respond. No safety checklists or routing scripts. Crisis and grey-area flags can both be true simultaneously.

### 10.4 Output Safety — Response Validation (`agent/safety/response_validator.py`)

After `GRAPH.invoke()`, `validate_response(response.content)` scans the reply text before delivery. Receives `response.content` (string) from the `ResponseFormat` object — not the whole object.

**Six blocked categories:**

| Category | Examples |
|---|---|
| Harmful advice | "kill yourself", "hurt yourself" |
| Medical diagnosis | "You have depression", "عندك إكتئاب" |
| Medication advice | "stop your medication" |
| Refusal patterns | "I can't discuss this" |
| Hotlines / emergency numbers | 911, 988, "call the hotline" |
| Routing scripts (non-crisis) | "your life has value", "find someone nearby" |

**Streaming Validation & Repair flow:** The agent streams its response via WebSockets in real-time. After the stream completes, `validate_response()` scans the accumulated reply text. 
- If validation fails, a `{"type": "clear"}` signal is dispatched over the WebSocket to erase the unsafe message from the user's UI.
- The system automatically triggers a repair loop, appending the flagged output and asking the LLM to correct itself, up to `SAFETY_MAX_OUTPUT_RETRIES` (3 times).
- If all retries fail, a hardcoded fallback (`FALLBACK_RESPONSE`) is sent instead.
- Unsafe outputs are flagged in the database (`safety_flag="UNSAFE_OUTPUT"`) and excluded from future context loops to protect the agent's memory from its own mistakes.

### 10.5 Safety Flag → DB Mapping

Detection results are mapped to the `safety_flag` column in the `messages` table before `save_message()` is called:

| Detection Result | `safety_flag` Value |
|---|---|
| `crisis_flag = True` | `"RED"` |
| `grey_area_flag = True` (no crisis) | `"ORANGE"` |
| Both false | `None` |

`YELLOW` and `GRAY` are reserved for future use (e.g., mild risk indicators).

### 10.6 RAG vs. Safety — Qdrant Collections

| | RAG | Crisis Safety |
|---|---|---|
| Collection | `amaan_knowledge` | `crisis_knowledge` |
| Embedding Model | BGE-M3 (1024-dim) | MiniLM-L6-v2 (384-dim) |
| Stored Content | ~36,700+ knowledge chunks | ~20 crisis phrases |
| Runs On | Agent tool call (when needed) | Every message, always |

> We may later use google embeding 2 if the usage is feasable

---

## 11. Physical Project Structure

```
backend/
│
├── manage.py                           # Django command-line execution entry point
├── logger.py                           # Centralized system logger
├── Logs/                               # Runtime log outputs (gitignored)
│   └── aman.log
│
├── core/                               # Django System Core
│   ├── settings.py                     # Root Django configurations
│   ├── urls.py                         # Root URL routing table
│   ├── asgi.py                         # ASGI asynchronous configuration
│   └── wsgi.py                         # WSGI synchronous fallback configuration
│
├── api/                                # App: Authentication Pages & REST APIs
│   ├── serializers.py                  # Register/Login schema validators
│   ├── urls.py                         # Auth URLs (/api/v1/auth/* and pages)
│   └── views.py                        # LoginPageView renders the combined HTML template for login.
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
├── agent/                              # Module: Independent LangGraph AI Engine
│   ├── config.py                       # LLM variables, Qdrant settings, context limits
│   ├── graph.py                        # LangGraph DAG compilation
│   ├── llm.py                          # Ollama LLM model initializations
│   ├── runner.py                       # Synchronous thread-safe entry point
│   │
│   ├── prompts/                        # System prompt layers
│   │   ├── builder.py                  # Dynamic prompt assembly
│   │   ├── core.py                     # Main agent rules and persona
│   │   ├── safety.py                   # Crisis/grey-area mode definitions and rules
│   │   ├── cultural.py                 # Islamic/Arabic guidelines
│   │   ├── tools.py                    # RAG tool usage instructions
│   │   ├── summary.py                  # Summarization prompts
│   │   ├── title.py                    # Title generation prompts
│   │   └── dynamic.py                  # Prompt runtime context generator
│   │
│   ├── memory/                         # History compaction
│   │   ├── history.py                  # DB history loader
│   │   └── summarizer.py               # Rolling summaries compiler
│   │
│   ├── tools/                          # LangGraph tool implementations
│   │   ├── __init__.py
│   │   └── rag.py                      # RAG search tool (@tool decorated)
│   │
│   └── safety/                         # Two-stage safety firewall
│       ├── __init__.py
│       ├── crisis_detector.py          # Keyword + semantic crisis detection
│       ├── grey_area_detector.py       # Keyword + regex grey-area detection
│       └── response_validator.py       # Output validation and repair flow
│
└── knowledge/                          # RAG ingestion (one-time setup — not part of running app)
    ├── ingest.py                       # Main ingestion pipeline entry point
    ├── embeddings.py                   # Embedding and Qdrant upsert logic
    └── sources/                        # Raw knowledge source files
        ├── ShifaaAMHC/                 # Arabic Q&A Excel files
        ├── *.pdf                       # Mental health publications
        ├── referral_directory.txt      # Arabic-region hotlines and resources
        └── crisis_contacts_arabic.txt  # Crisis contact numbers by country
```

---

## 12. Database Model Design

### 12.1 User Model (`backend/users/models.py`)
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

### 12.2 Chat Model (`backend/chats/models.py`)
```python
class Chat(models.Model):
    chat_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="id")
    title = models.CharField(max_length=255, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)
```

### 12.3 Message Model (`backend/chats/models.py`)
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
*`is_active = TRUE` → included in agent context. `is_active = FALSE` → summarized and excluded.*
*`safety_flag` accepted values: `RED`, `ORANGE`, `YELLOW`, `GRAY`.*

### 12.4 Summary Model (`backend/chats/models.py`)
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

## 13. Complete Endpoint Routing Matrix

All routes mapped in Django apps are detailed in `URL_API_Mapping.md`. Note that the web interface is now a separate React SPA (Vite/Tailwind) that consumes these REST endpoints directly, completely bypassing Django's traditional HTML templates.

- **POST** `/api/v1/auth/register/` — Registration
- **POST** `/api/v1/auth/login/` — Login
- **POST** `/api/v1/auth/refresh/` — Refresh Token
- **POST** `/api/v1/auth/logout/` — Invalidation
- **GET/PUT/DELETE** `/api/v1/users/me/` — Profile management
- **GET/POST** `/api/v1/chats/` — Chat list and instantiation
- **GET/DELETE** `/api/v1/chats/<uuid:chat_id>/` — Retrieve conversation history or delete
- **WebSocket** `/ws/chat/<uuid:chat_id>/` — Send real-time messages and receive streaming agent chunks via ASGI/Daphne.

---

## 14. Tech Stack Summary

- **Frontend Application**: React SPA (Vite + Tailwind CSS v4)
- **Frontend State Management**: Zustand
- **Backend Web Framework**: Django + Django REST Framework (DRF)
- **WebSocket Server**: Daphne / Django Channels
- **Authentication**: JWT (JSON Web Tokens) via `djangorestframework-simplejwt`
- **Agent Orchestrator**: LangGraph + LangChain Core
- **LLM Engine**: Ollama (running locally), Groq API, or cloud APIs (Deepseek-V4)
- **Vector Database**: Qdrant (running locally via Docker on localhost:6333)
- **RAG Embedding Model**: BAAI/bge-m3 (1024-dim, multilingual) or google embeding 2 (if fesable)
- **Crisis Embedding Model**: all-MiniLM-L6-v2 (384-dim, lightweight) or google embeding 2 (if fesable)
- **Relational Database**: PostgreSQL (accessed via Django ORM, running via Docker)
- **Logger**: Python standard `logging` (custom configured in `backend/logger.py`)
- **Package Manager**: UV

---

## 15. Recent Updates (Changelog)

### v6.1 - UI Expansion & Groq Integration
- **Frontend Restructuring**: Split the single-page app into a public Landing Page (`/`) and a protected Chat Dashboard (`/app`).
- **Settings & Preferences**: Added a user settings modal supporting dynamic UI language switching, dark mode (with persistent memory), and user profile updates.
- **Agent Reasoning**: Switched the core "thinking" model to `openai/gpt-oss-120b` via the Groq API. Created a custom `LLMWrapper` in `agent/llm.py` to seamlessly stream and capture `<think>` tags within LangChain.
- **Chat Management**: Users can now directly rename (`PATCH`) and delete (`DELETE`) individual conversations from the sidebar UI.
- **Data Privacy**: Added a "Delete History" endpoint (`/api/v1/chats/history/`) that wipes all user chats from PostgreSQL and purges their long-term extracted facts from the Qdrant vector database.
- **Authentication Enhancements**: Added an endpoint to change user passwords (`/api/v1/users/change-password/`) with validation rules.
- **Admin Panel**: Registered the `Chat` and `Message` models in the Django admin panel.
- **Safety Fixes**: Resolved a critical database crash where the `UNSAFE_OUTPUT` safety flag exceeded the 10-character limit by renaming it to `UNSAFE`.
