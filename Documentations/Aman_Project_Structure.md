# Aman — Project Structure & Directory Layout v2
### System Architecture and File Mapping

Aman is a bilingual (Arabic/English) AI-powered Emotional Wellness Support Agent built on **Django** (for backend REST API, user management, and template rendering) and **LangGraph / LangChain** (for conversational orchestration and agentic reasoning).

This document provides a comprehensive guide to the physical and logical structure of the **Aman Reformed** codebase. It outlines the role of each directory, file, and component, showing how the Django web framework interfaces with the framework-agnostic AI agent engine, RAG ingestion components, and safety systems.

---

## 1. High-Level Workspace Directory Layout

The physical structure of the workspace is organized into three major zones:
1. **Root Configurations & Environments**: Packaging, dependency locks, and project licensing.
2. **Technical Documentations**: Specifications, schemas, API guides, and reference materials.
3. **Django Backend Application**: The web server, REST apps, RAG knowledge ingestion pipelines, and the core AI agent engine.

```
/home/opendude/Documents/Aman Reformed/
├── .gitignore                          # Standard git ignore definitions
├── .python-version                     # Local python runtime version lock (e.g. 3.12)
├── LICENSE                             # Project licensing agreement
├── README.md                           # Quick-start setup & execution guide
├── pyproject.toml                      # Modern Python packaging configuration (uv/pep-518)
├── uv.lock                             # Strict python dependency lockfile (managed by uv)
├── docker-compose.yml                  # Docker services definition (PostgreSQL, Qdrant)
├── Documentations/                     # Technical specifications, schema, and API guides
│   ├── Aman_DB_Tables.md               # Precise database schema & cascade mapping
│   ├── Aman_Project_File.md            # Comprehensive system specification (v6)
│   ├── Aman_Project_Structure_v1.md    # Legacy project structure documentation
│   ├── Aman_Project_Structure_v2.md    # [THIS FILE] Updated structure & layout documentation
│   ├── Aman_URL_API_Mapping.md         # Precise URL/API route mappings & JSON schemas
│   └── RAG Knowledge Base for Aman.txt # RAG knowledge base details and research notes
└── backend/                            # Root Backend Project Directory
    ├── manage.py                       # Django command-line execution entry point
    ├── logger.py                       # Centralized runtime logging utility
    ├── .env                            # Local environment secrets and configuration overrides
    ├── Logs/                           # Output directory for application logs (gitignored)
    │   └── aman.log                    # Main system log output file
    │
    ├── core/                           # Django Project Settings & Root Routing
    │   ├── __init__.py
    │   ├── settings.py                 # Core settings, database connection, and middleware
    │   ├── urls.py                     # Root URL routing configuration
    │   ├── asgi.py                     # ASGI server entry point for asynchronous runs
    │   └── wsgi.py                     # WSGI server entry point for synchronous web servers
    │
    ├── api/                            # App: Authentication Pages & REST APIs
    │   ├── serializers.py              # Register/Login schema validators
    │   ├── urls.py                     # Auth URLs (/api/v1/auth/* and pages)
    │   └── views.py                    # Page rendering & token generation endpoints
    │
    ├── users/                          # App: Profile Management & Settings
    │   ├── models.py                   # User DB Model (UUID primary key "id")
    │   ├── serializers.py              # Profile data serialization
    │   ├── urls.py                     # Profile settings URLs
    │   └── views.py                    # Profile CRUD APIs & settings page view
    │
    ├── chats/                          # App: Chat Core, Dashboard & Message Delivery
    │   ├── models.py                   # Chat, Message, and Summary DB models
    │   ├── serializers.py              # Message payloads & model selection validator
    │   ├── urls.py                     # Chat room pages and CRUD URLs
    │   └── views.py                    # Bridges REST views with the LangGraph runner
    │
    ├── agent/                          # Module: Pure Python LangGraph AI Engine
    │   ├── __init__.py
    │   ├── apps.py                     # Agent configuration initialization helper
    │   ├── config.py                   # Context sizes, model names, and Qdrant settings
    │   ├── emotion_estimator.py        # Text classification pipeline for extracting emotion
    │   ├── graph.py                    # LangGraph DAG compilation and node execution routing
    │   ├── llm.py                      # Ollama/Cloud client, ThinkingLLMWrapper, and title utility
    │   ├── runner.py                   # Synchronous thread-safe agent entry point
    │   │
    │   ├── prompts/                    # Multi-layered Bilingual Prompt Templates
    │   │   ├── builder.py              # Dynamically compiles prompts per request
    │   │   ├── core.py                 # Core persona, response formats, and tone
    │   │   ├── safety.py               # Crisis and grey-area instructions
    │   │   ├── cultural.py             # Sensitivity rules for Arabic/Islamic context
    │   │   ├── tools.py                # LangGraph tool calling instructions
    │   │   ├── summary.py              # Conversation summarization prompt template
    │   │   ├── title.py                # Auto-title generation system instructions
    │   │   └── dynamic.py              # Prompt runtime context generator
    │   │
    │   ├── memory/                     # Context Management & History Compaction
    │   │   ├── history.py              # Database history loader and formatter
    │   │   └── summarizer.py           # Background rolling summaries compiler
    │   │
    │   ├── tools/                      # Tool Definitions
    │   │   ├── __init__.py
    │   │   └── rag.py                  # RAG search tool (@tool decorated)
    │   │
    │   └── safety/                     # Two-Stage Safety Firewall
    │       ├── __init__.py
    │       ├── crisis_detector.py      # Keyword + semantic crisis checks
    │       ├── grey_area_detector.py   # Keyword + regex cultural risk checks
    │       └── response_validator.py   # Output scans and LLM-assisted repair flow
    │
    └── knowledge/                      # RAG Ingestion Pipeline (One-time setup scripts)
        ├── ingest.py                   # Main ingestion orchestrator
        ├── embeddings.py               # HuggingFace Embeddings and Qdrant client upserts
        └── sources/                    # Raw text, Excel, and PDF knowledge sources
            ├── ShifaaAMHC/             # ~36,700 Arabic consultation QA records (Excel)
            ├── referral_directory.txt  # Hotlines, online support platforms, and therapist finder
            └── *.pdf                   # DBT/CBT textbooks, guidelines, and manuals
```

---

## 2. Deep-Dive Directory Audit (Web Framework Layer)

### 2.1 Roots & Project Configs (Root Directory)
*   `pyproject.toml` & `uv.lock`: Configuration files for package management with `uv` for reproducible environments. Key dependencies include `django`, `djangorestframework`, `djangorestframework-simplejwt`, `langchain-ollama`, `langgraph`, `qdrant-client`, `sentence-transformers`, and `pydantic`.
*   `Documentations/`: Houses core technical specification files, URL mapping matrixes, database DDLs, and references.
*   `backend/.env`: Configures environment-specific variables including Django keys, PostgreSQL credentials, local Ollama URLs, and Qdrant instances.

### 2.2 Django System Core (`backend/core/`)
This is the root configuration directory of the Django project.
*   `settings.py`: Configures **JWT authentication** (`rest_framework_simplejwt`), custom User model mapping (`AUTH_USER_MODEL = "users.User"`), CORS settings (`corsheaders`), PostgreSQL database configuration (`DATABASES`), and static assets handling.
*   `urls.py`: The root URL routing file. Delegates page routing and API routing by nesting app-level `urls.py` files.
*   `asgi.py` & `wsgi.py`: Standard entry points for web servers. ASGI handles modern asynchronous operations, while WSGI provides standard synchronous compatibility.

### 2.3 Authentication App (`backend/api/`)
This app handles user onboarding, sign-in pages, and JWT access/refresh token generation.
*   `serializers.py`: Defines `RegisterSerializer` (creates accounts, handles password encryption through Django ORM) and `LoginSerializer`.
*   `urls.py`: Maps the login/register HTML pages and the JWT REST API endpoints (`/api/v1/auth/*`).
*   `views.py`: 
    *   *Pages*: `LoginPageView` renders the combined HTML template for both login and registration.
    *   *APIs*: `RegisterView` (signs up user, returns access/refresh tokens), `LoginView` (authenticates credentials, returns tokens), and `LogoutView` (blacklists refresh token and redirects to login).

### 2.4 Profile Management App (`backend/users/`)
Manages user accounts, profiles, and preferences.
*   `models.py`: Defines the `User` model, extending `AbstractBaseUser`. Key columns are `id` (UUID primary key), `name`, `email` (unique lookup), `birthdate`, `gender` (male/female choices), `country` (2-letter country code), and `creation_date`. Uses custom `UserManager` to ensure password safety via bcrypt.
*   `serializers.py`: Defines `UserSerializer` for structured JSON representation, enforcing read-only safety for primary keys and emails.
*   `urls.py`: Maps the user configuration settings web interface and the REST endpoints.
*   `views.py`:
    *   *Pages*: `SettingsPageView` renders the user settings interface.
    *   *APIs*: `UserMeView` handles `GET` (fetch profile details), `PUT` (update profile partially), and `DELETE` (completely purge account and cascade all related chats/messages).

### 2.5 Chat & Product App (`backend/chats/`)
The core domain of the product, managing conversations, active session rendering, and REST endpoints for message delivery.
*   `models.py`:
    *   `Chat`: Represents a conversation thread. Mapped to table `chats`. Linked to `User` via foreign key `user` (DB column name `id`).
    *   `Message`: Stores individual entries. Linked to `Chat` via `chat` (DB column `chat_id`). Contains columns like `role` (user/assistant), `content`, `creation_date`, `emotional_state` (JSONField tracking user emotions), `safety_flag`, and `is_active` (for context control).
    *   `Summary`: Rolling memory compression block linked to `Chat`. Mapped to table `summaries` and ordered by `version`.
*   `serializers.py`: Models conversion to/from JSON. Contains request validator `MessageRequestSerializer` verifying incoming user prompt `content` and preferred reasoning `model` ("1" for deep reasoning, "2" for fast responses).
*   `urls.py`: Routes pages like the `/dashboard/` and `/chat/<uuid>/` as well as the API routes under `/api/v1/chats/`.
*   `views.py`:
    *   *Pages*: `DashboardPageView` (user dashboard listing active sessions) and `ChatRoomPageView` (main interactive interface).
    *   *APIs*: `ChatListView` (lists active user chats / creates a new session), `ChatDetailView` (retrieves active message history / deletes specific session), and `MessageView` (accepts user prompt, triggers AI agent pipelines synchronously, returns assistant response). It also handles STT and TTS integrations for voice.

---

## 3. AI Agent Core (`backend/agent/`)

The `agent` directory represents a framework-agnostic AI orchestrator. It uses **LangGraph** to process user prompts, maintain context-aware state, and run tools. It has NO imports from Django, ensuring modularity.

### 3.1 Prompts Layer (`backend/agent/prompts/`)
System prompts are assembled dynamically to guide the LLM's behavior:
*   `builder.py`: Combines static prompt segments and injects dynamic context (language, emotional state, safety warnings).
*   `core.py`: Defines the primary agent persona, rules, and structured JSON response requirements.
*   `safety.py`: Outlines rules for handling crises (RED mode) and culturally sensitive grey-area topics (ORANGE mode).
*   `cultural.py`: Sensitivity rules tailored to the Arabic and Islamic MENA region.
*   `tools.py`: Instructions on when and how to call the RAG system.
*   `summary.py`: Directives for generating clean rolling context summaries.
*   `title.py`: Directives for generating short, context-appropriate conversation titles.
*   `dynamic.py`: Formats current session flags into the dynamic context layer.

### 3.2 Memory & Context Management (`backend/agent/memory/`)
Provides context management, feeding recent messages to the LLM and archiving historical ones to keep processing windows slim.
*   `history.py`: Accesses Django models via ORM to retrieve active conversation histories and latest summaries. Prepares the list of LangChain message classes.
*   `summarizer.py`: Houses background thread utilities to compile old messages into rolling summaries when conversation length thresholds are met.

### 3.3 LangGraph Architecture (`backend/agent/graph.py` & `tools/`)
Compiles the LangGraph state machine which controls the reasoning lifecycle.
*   `graph.py`: Defines the `StateGraph` state structure, routing logic, nodes, and compiles the final executables. It binds tools directly to the LLM.
*   `tools/rag.py`: Implements the `rag_search` tool which performs semantic lookups in the Qdrant `amaan_knowledge` collection.

### 3.4 Safety Module (`backend/agent/safety/`)
A dual-stage firewall protecting both input and output.
*   `crisis_detector.py`: Scans incoming text for self-harm or severe crises using fast keyword checks and deep semantic matching against `crisis_knowledge`.
*   `grey_area_detector.py`: Scans incoming text for sensitive or high-risk topics (sexuality, abuse, addiction, divorce) using keywords and regex mapping.
*   `response_validator.py`: Audits assistant text responses for diagnostic statements, prescription suggestions, numbers, or harmful guidance, triggering repair routines if flags fire.

---

## 4. RAG & Ingestion System (`backend/knowledge/`)

The RAG (Retrieval-Augmented Generation) infrastructure operates as a separate ingestion layer and runtime search tool to ground the agent in verified mental health and regional guidelines.

### 4.1 Vector Storage Layout
*   **Vector Database**: Qdrant running locally via Docker at `localhost:6333`.
*   **Embedding Model (RAG)**: BAAI/bge-m3 (1024 dimensions, L2-normalized) or cloud alternative (Google Embeddings 2).
*   **Embedding Model (Crisis)**: all-MiniLM-L6-v2 (384 dimensions) or cloud alternative (Google Embeddings 2).
*   **Collections**:
    *   `amaan_knowledge`: Stores chunks of general counseling files, textbooks, and datasets.
    *   `crisis_knowledge`: Stores ~20 crisis semantic anchors for instant safety checks.

### 4.2 Ingestion & Chunking Logic (`knowledge/ingest.py`)
All cleanings and chunks are compiled using a one-time utility:
*   **Text Normalization**: Standardizes Arabic characters (alefs, ta marbutas), strips diacritics, and normalizes whitespaces. Duplicate chunks are purged via SHA-256 matching.
*   **Chunking Strategy**:
    *   *Excel Datasets (ShifaaAMHC)*: Split row-by-row into QA pairs: `العنوان: [title] \n السؤال: [question] \n الإجابة: [answer] \n التشخيص: [diagnosis]`.
    *   *Textbooks & Guidelines (PDF/URL/Text)*: Paragraph-aware chunking with overlapping limits (40-350 words, 30-word overlap) to preserve contextual boundaries.

---

## 5. End-to-End Orchestration Workflow

When a user posts a message to `/api/v1/chats/<uuid>/message/`, the system executes the following synchronous, thread-safe sequence:

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client (Web/Voice)
    participant Django as Django View (MessageView)
    participant Safety as Safety Firewall (agent/safety/)
    participant Memory as Memory Manager (agent/memory/)
    participant Graph as LangGraph Engine (agent/graph.py)
    participant LLM as LLM (Ollama / Cloud)
    participant DB as PostgreSQL DB
    participant Qdrant as Qdrant Vector DB

    Client->>Django: POST /message/ (Prompt text or Audio)
    Note over Client,Django: STT translates Voice Input to Text if audio sent
    
    rect rgb(240, 248, 255)
        Note over Django,Safety: Stage 1: Input Safety Checks
        Django->>Safety: Run Input Safety (crisis_detector, grey_area_detector)
        Safety->>Qdrant: Semantic Crisis Check (crisis_knowledge)
        Qdrant-->>Safety: Semantic Similarity Result
        Safety-->>Django: Return Flags (crisis_flag, grey_area_flag)
    end
    
    Django->>Graph: Emotion Estimator (agent/emotion_estimator.py)
    Graph-->>Django: Return Emotion Result

    Django->>Memory: Load History (load_history)
    Memory->>DB: Fetch Active Messages & Latest Summary
    DB-->>Memory: Messages / Summary
    Note over Memory: Prepend summary as SystemMessage;\nAppend active history;\nAppend emotion to HumanMessage
    Memory-->>Django: Compiled History Sequence

    rect rgb(240, 240, 240)
        Note over Memory: Background Tasks (Threaded)
        opt History size >= 40 messages
            Memory-->>DB: Run Summarizer thread (is_active=False on old 50%; create Summary)
        end
        opt Title is "Untitled Chat" & first message
            Memory-->>DB: Run Title Generator thread (saves short title to Chat)
        end
    end

    Django->>Graph: Invoke State Machine (GRAPH.invoke)
    Graph->>LLM: Pass System Prompt (Builder) + History Sequence
    
    opt LLM Decides RAG search is needed
        Graph->>Qdrant: Semantic Search Query (amaan_knowledge)
        Qdrant-->>Graph: Return Top-3 Passages
        Graph->>LLM: Append ToolMessage passages to Context
    end
    
    LLM-->>Graph: Return Structured JSON / Parsed Plain Text (ResponseFormat)
    Graph-->>Django: Return Content

    rect rgb(255, 240, 240)
        Note over Django,Safety: Stage 2: Output Safety Check
        Django->>Safety: Run Output Validation (validate_response)
        opt Content fails safety policy
            Safety->>LLM: Run repair_response() or fallback to hardcoded reply
        end
        Safety-->>Django: Return Validated Safe Content
    end

    Django->>DB: Save User & Assistant messages (save_message)
    Note over DB: Map safety_flag (RED for Crisis, ORANGE for Grey Area)
    Django->>Client: Send JSON Response (Text + TTS Audio URL/Data)
```

---

## 6. Database & API Routing Reference

### 6.1 Database Models Schema
*   **User (`users.User`)**: UUID primary key. Stores registration fields (`name`, `email`, `birthdate`, `gender`, `country`, `creation_date`). Uses bcrypt for passwords.
*   **Chat (`chats.Chat`)**: UUID primary key. Linked to `User` via foreign key `user` (DB column name `id`). Stores title, creation, and modify dates.
*   **Message (`chats.Message`)**: UUID primary key. Linked to `Chat` via foreign key `chat` (DB column `chat_id`). Stores `role` ('user'/'assistant'), `content`, `creation_date`, `emotional_state` (JSONB containing emotion and confidence), `safety_flag` (`RED`, `ORANGE`, `None`), and `is_active` (boolean controlling context window inclusion).
*   **Summary (`chats.Summary`)**: UUID primary key. Linked to `Chat` via foreign key `chat` (DB column `chat_id`). Stores rolling summary text, emotional state summary, safety flags, and `version` (auto-incrementing).

### 6.2 Endpoint Routing Table

All page views and REST endpoints are consolidated under Django apps, routing requests as follows:

| Category | Method | Path | View Class | Target / Purpose |
| :--- | :---: | :--- | :--- | :--- |
| **Auth Pages** | `GET` | `/login/` | `LoginPageView` | Renders combined Login/Registration Form |
| **Auth API** | `POST` | `/api/v1/auth/register/` | `RegisterView` | Signs up user, generates JWT tokens |
| **Auth API** | `POST` | `/api/v1/auth/login/` | `LoginView` | Validates login, issues JWT tokens |
| **Auth API** | `POST` | `/api/v1/auth/refresh/` | `TokenRefreshView` | Standard simplejwt token refresher |
| **Auth API** | `POST` | `/api/v1/auth/logout/` | `LogoutView` | Blacklists refresh token, redirects to `/login/` |
| **Profile Page** | `GET` | `/settings/` | `SettingsPageView` | Renders Settings Panel |
| **Profile API** | `GET` | `/api/v1/users/me/` | `UserMeView` | Retrieves current profile settings |
| **Profile API** | `PUT` | `/api/v1/users/me/` | `UserMeView` | Updates profile details |
| **Profile API** | `DELETE` | `/api/v1/users/me/` | `UserMeView` | Purges account (cascades all chats/messages) |
| **Chat Pages** | `GET` | `/dashboard/` | `DashboardPageView` | Renders dashboard showing list of conversations |
| **Chat Pages** | `GET` | `/chat/<uuid:chat_id>/` | `ChatRoomPageView` | Renders active web conversation window |
| **Chat API** | `GET` | `/api/v1/chats/` | `ChatListView` | Returns active chats ordered by modify date |
| **Chat API** | `POST` | `/api/v1/chats/` | `ChatListView` | Instantiates a new empty conversation session |
| **Chat API** | `GET` | `/api/v1/chats/<uuid:chat_id>/` | `ChatDetailView` | Retrieves active chats history |
| **Chat API** | `DELETE` | `/api/v1/chats/<uuid:chat_id>/` | `ChatDetailView` | Deletes a conversation session |
| **Agent API** | `POST` | `/api/v1/chats/<uuid:chat_id>/message/` | `MessageView` | User prompt/audio entry; streams real-time text & TTS audio |

---

## 7. Key Architectural Decisions

1.  **Strict Separation of AI and Web Routing**: The `agent/` folder is framework-agnostic. All DB queries within it are routed through specialized loader and writer utility functions in `agent.memory.history.py` (which use safe Django ORM calls).
2.  **Dual-Stage Safety Firewall**: The system runs input checks *before* prompt assembly (to adjust prompt parameters and intercept crises) and output checks *after* compilation (to validate content against diagnostic/medication filters).
3.  **Thread-Safe Background Operations**: Title generation and rolling summarizations run in separate `threading.Thread` instances. This prevents slow LLM processing from blocking the main request/response lifecycle. Connections are safely handled using Django's `close_old_connections()` in `finally` blocks.
4.  **Flexible Local and Cloud Routing**: The system's LLM components (`agent/llm.py` and `agent/config.py`) support running local Ollama instances (`gemma4:26b` / `gemma4:e2b`) or routing queries to cloud APIs (like DeepSeek-V4 or Google API wrappers), making it adaptable to hardware limitations.
5.  **Bilingual Dynamic Prompting**: System prompt layers are assembled dynamically per call based on inferred context, ensuring high quality in both Arabic and English.
6.  **Integrated Voice Pipeline**: Voice transcription (Whisper STT) and speech synthesis (Coqui/Piper TTS) are native components of the message pipeline, enabling hands-free communication flows.
