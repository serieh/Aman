# System Architecture

Aman uses a multi-agent framework orchestrated with LangGraph, moving away from a single end-to-end large language model call. This allows each cognitive function (perception, safety, memory, retrieval, generation) to be traced and evaluated independently.

![System Architecture](images/System%20Architecture%20Diagram.png)

## High-Level Components

### Frontend (React + Vite)
The client interface is built on React 19 and Vite. It prioritizes a calm, distraction-free layout. State management is handled by Zustand, coordinating chat input, conversation history, and multimodal (voice/text) session state without deep prop drilling.

### Backend API (Django & FastAPI)
- **Django**: Manages relational data (users, chat threads, messages) and handles WebSocket streaming via Daphne and Django Channels.
- **FastAPI**: Manages guest chat and voice interactions to isolate high-throughput, non-authenticated requests.

### AI Orchestrator (LangGraph)
The core of the framework is a directed graph that governs the turn flow:
1. **Preparation**: Loads session state, conversation history, and user profiles.
2. **Reasoning Loop**: The language model agent evaluates the user's message and invokes tools (e.g., RAG) if external context is needed.
3. **Finalization**: Executes output safety validation, memory persistence, long-term memory extraction, and chat title generation.

## Conversational Modes

Both modes are powered by the same underlying model (Groq `gpt-oss-120b`), changing only the depth of retrieval and reasoning.
- **Fast Mode**: Skips the retrieval pipeline entirely for quick emotional support (target latency ≤ 15s).
- **Thinking Mode**: Engages the RAG pipeline to ground answers in the mental-health knowledge base (target latency ≤ 30s).

## Data Stores
- **PostgreSQL**: Stores normalized user identities, chat metadata, message logs, and context summaries.
- **Qdrant**: Stores semantic vector embeddings across three logical collections:
  - `amaan_knowledge`: General clinical and cultural Q&A.
  - `crisis_knowledge`: Dedicated crisis-handling context.
  - `user_memory`: Extracted biographical facts for long-term personalization.
