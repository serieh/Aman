# Aman — Project Structure & Directory Layout
### System Architecture and File Mapping

Aman is a bilingual (Arabic/English) AI-powered Emotional Wellness Support Agent built on **Django** (for backend REST API, user management, and page rendering) and **LangGraph / LangChain** (for conversational orchestration and agentic reasoning).

This document provides a comprehensive guide to the physical and logical structure of the **Aman Reformed** codebase. It outlines the role of each directory, file, and component, showing how the Django web framework interfaces with the framework-agnostic AI agent engine.

---

## 1. High-Level Workspace Directory Layout

The physical structure of the workspace is split into two major zones: the root configurations/management scripts, and the Django backend package (which contains the REST apps and the AI agent core).

```
/home/opendude/Documents/Aman Reformed/
├── .gitignore                          # Standard git ignore definitions
├── .python-version                     # Local python runtime version lock (e.g. 3.12)
├── LICENSE                             # Project licensing agreement
├── README.md                           # Quick-start setup & execution guide
├── pyproject.toml                      # Modern Python packaging configuration (uv/pep-518)
├── uv.lock                             # Strict python dependency lockfile (managed by uv)
├── Documentations/                     # Technical specifications, schema, and API guides
│   ├── Aman_Project_File_v4.md         # Comprehensive system specification
│   ├── Tables.md                       # Precise database schema & cascade mapping
│   ├── aman_url_map_clean_architecture_v_5.md # Legacy URL mapping guide
│   ├── Project_Structure.md            # [THIS FILE] Project structure documentation
│   └── URL_API_Mapping.md              # [NEW FILE] Precise URL/API route mapping
└── backend/                            # Unified Django Project Directory
    ├── manage.py                       # Django command-line execution entry point
    ├── logger.py                       # Centralized runtime logging utility
    ├── Logs/                           # Output directory for application logs (gitignored)
    │   └── aman.log                    # Main system log output file
    ├── backend/                        # Root Django settings & system routing configuration
    ├── api/                            # Django App: Authentication pages, APIs, and token management
    ├── users/                          # Django App: User profile endpoints and settings panel
    ├── chats/                          # Django App: Main chat views, REST interfaces, and template pages
    └── agent/                          # Pure Python module: LangGraph AI Agent Orchestrator
```

---

## 2. Deep-Dive Directory Audit

### 2.1 Roots & Project Configs (Root Folder)
*   `pyproject.toml` & `uv.lock`: Use modern package management with `uv` for fast, reproducible environments. Key dependencies include `django`, `djangorestframework`, `djangorestframework-simplejwt`, `langchain-ollama`, `langgraph`, and `pydantic`.
*   `Documentations/`: Contains all university graduation project specifications, tables, architecture guides, and reference documents.

### 2.2 Django System Core (`backend/backend/`)
This is the root configuration directory of the Django project.
*   `__init__.py`: Package marker.
*   `settings.py`: Integrates Django features. Configures **JWT authentication** (`rest_framework_simplejwt`), custom User model mapping (`AUTH_USER_MODEL = "users.User"`), CORS settings (`corsheaders`), PostgreSQL database configuration (`DATABASES`), and static assets handling.
*   `urls.py`: The root URL routing file. Delegates page routing and API routing by nesting app-level `urls.py` files.
*   `asgi.py` & `wsgi.py`: Standard entry points for web servers. ASGI is configured for modern asynchronous operations, while WSGI provides standard synchronous compatibility.

### 2.3 Authentication App (`backend/api/`)
This app handles all authentication-related features. It is uniquely named `api` in the code, but represents the Account and Authentication layer.
*   `serializers.py`: Defines `RegisterSerializer` (creates accounts, handles password encryption through Django ORM) and `LoginSerializer`.
*   `urls.py`: Maps the login/register HTML pages and the JWT REST API endpoints (`/api/v1/auth/*`).
*   `views.py`: 
    *   *Pages*: `LoginPageView` and `RegisterPageView` render HTML templates.
    *   *APIs*: `RegisterView` (signs up user, returns access/refresh tokens), `LoginView` (authenticates via Django's auth system, returns tokens), and `LogoutView` (blacklists refresh token and redirects to login).

### 2.4 Profile Management App (`backend/users/`)
Manages accounts and preferences.
*   `models.py`: Defines the `User` model, extending `AbstractBaseUser`. Key columns are `id` (UUID primary key), `name`, `email` (unique lookup), `birthdate`, `gender` (male/female choices), `country` (2-letter country code), and `creation_date`. Uses custom `UserManager` to ensure password safety via bcrypt.
*   `serializers.py`: Defines `UserSerializer` for structured JSON representation, enforcing read-only safety for primary keys and emails.
*   `urls.py`: Maps the user configuration web interface and the REST endpoints.
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
    *   *APIs*: `ChatListView` (lists active user chats / creates a new session), `ChatDetailView` (retrieves active message history / deletes specific session), and `MessageView` (accepts user prompt, triggers AI agent pipelines synchronously, returns assistant response).

---

## 3. AI Agent Core (`backend/agent/`)

The `agent` directory represents a framework-agnostic AI orchestrator. It uses **LangGraph** to process user prompts and maintain context-aware state. It has NO imports from Django, making it modular.

```
backend/agent/
├── config.py                           # System configurations (LLM models, context limits)
├── graph.py                            # LangGraph state machine structure and nodes
├── llm.py                              # Ollama client initialization & utility actions
├── runner.py                           # Thread-safe pipeline execution wrapper
├── memory/                             # Conversational context and background compression
│   ├── history.py                      # DB loader and history formatter
│   └── summarizer.py                   # Background rolling summary compilation
└── prompts/                            # Multi-layered bilingual system prompts
    ├── builder.py                      # Joins static prompts and builds dynamic system context
    ├── core.py                         # Defines agent persona, response formats, and tone
    ├── safety.py                       # Instructions on crisis routing (RED, ORANGE, etc.)
    ├── cultural.py                     # Sensitivity guidelines for Arabic/Islamic settings
    ├── tools.py                        # System instructions on tools (RAG, Vision)
    ├── summary.py                      # Compressing historical context instructions
    ├── title.py                        # Automated short chat title generation guidelines
    └── dynamic.py                      # Build dynamic context block (emotion, language, safety)
```

### 3.1 Orchestration Workflow

When the Django API endpoint `/api/v1/chats/<uuid>/message/` receives a POST request:
1. It validates parameters via `MessageRequestSerializer`.
2. It invokes `run_agent()` inside `backend/agent/runner.py`.
3. `run_agent()` triggers `load_history(chat_id)` from `agent.memory.history`.
    * If no prior messages exist and the title is "Untitled Chat", a **background thread** is started to generate a short, beautiful title via `title_generator()` in `agent.llm` and saves it.
4. `load_history()` reads active records from the `messages` table and the latest compiled block from the `summaries` table.
5. If the active messages exceed `MAX_MESSAGES_BEFORE_SUMMARY` (default: 40), `load_history()` spins off a **background thread** executing `run_summarization_background()` from `agent.memory.summarizer` to compress the oldest 50% of messages into a new `Summary` entry and mark them inactive (`is_active = False`).
6. A multi-layered prompt is assembled via `build_system_prompt()` (`agent.prompts.builder`), incorporating current emotional states and language preferences.
7. The LangGraph graph compiled in `agent.graph.GRAPH` is invoked with the compiled message sequence.
8. The LLM (via `agent.llm`) returns a structured `ResponseFormat` object parsing out text `content` and inferred `emotional_state`.
9. `run_agent()` persists both the user's message and the assistant's response to the database using `save_message()`, then updates `modify_date` in the `Chat` table.
10. The cleaned response is sent back to the Django view, which returns it as a clean JSON response.

---

## 4. Key Architectural Decisions

1.  **Strict Separation of AI and Web Routing**: The `agent/` folder is framework-agnostic. All DB queries within it are routed through specialized loader and writer utility functions in `agent.memory.history.py` (which use safe Django ORM calls).
2.  **Thread-Safe Background Operations**: Title generation and rolling summarizations run in separate `threading.Thread` instances. This prevents slow LLM processing from blocking the main request/response lifecycle. Connections are safely handled using Django's `close_old_connections()` in `finally` blocks.
3.  **Bilingual Dynamic Prompting**: System prompt layers are assembled dynamically per call based on inferred context, ensuring high quality in both Arabic and English.
