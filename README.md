# Aman

G'day! Welcome to **Aman**. This project is a bilingual (Arabic-English) emotional wellness support AI agent. It's built to provide safe, warm, and emotionally intelligent support for folks experiencing emotional distress, stress, or just needing a solid yarn when things get tough.

## Purpose

Aman aims to be a virtual shoulder to lean on. It's not a doctor (don't go asking it to prescribe you anything, mate!), but it provides factually grounded, culturally sensitive support, particularly tailored for the Arab and Islamic world. It uses an advanced RAG (Retrieval-Augmented Generation) pipeline and local AI models to keep conversations private, fast, and empathetic.

## Requirements

To get this beauty up and running, you'll need the following installed on your rig:

- **Docker** and **Docker Compose** (for spinning up the databases without the headache)
- **Node.js** (v18+) and **npm** (for the frontend magic)
- **Python** (v3.10+) and **uv** (the blazingly fast Python package installer)
- **Ollama** (running locally to serve up the AI models)

## Dependencies

Aman is built on the shoulders of giants. Here's what's powering it under the hood:

- **Backend:** Django, Django REST Framework, Channels (WebSockets for real-time chat)
- **Frontend:** React + Vite (for that snappy UI)
- **AI & Data:** LangChain, LangGraph, Sentence-Transformers, HuggingFace
- **Databases:** PostgreSQL (relational data) and Qdrant (vector storage for RAG and long-term memory)

## How to Run

Forget typing out twenty different commands. We've got a `Makefile` that does the heavy lifting for you:

### 1. Configure Environment Variables
Before running the application, set up your environment variables. Copy the `.env.example` file in the `backend/` directory to `.env`:
```bash
cp backend/.env.example backend/.env
```
Open `backend/.env` and fill in your keys (e.g., `GROQ_API_KEY`, `SECRET_KEY`, etc.).

### 2. Run the Stack

You can run the stack in one of two modes depending on whether you are using local models:

#### Mode A: Dev Stack (With Ollama Fallback)
This is the standard dev stack. It starts Docker containers (PostgreSQL & Qdrant), starts Ollama serve, runs database migrations, and spawns both the backend (Daphne) and frontend (Vite) dev server in parallel.
```bash
make dev
```

#### Mode B: Dev Stack (Cloud-Only / No Ollama)
If you do not want to run local Ollama models on your rig, run the cloud-only stack. This starts Docker containers, runs migrations, and spawns the backend and frontend. All background agent operations will route to Groq:
```bash
make dev-cloud
```

Once the servers are up, point your browser to `http://localhost:5173` and say hello to Aman!

### Individual Commands
If you prefer running components individually in separate terminals:
*   **Docker Databases**: `make up`
*   **Stop Databases**: `make down`
*   **Clean Caches & Stop**: `make clean`

---

## Credits & Acknowledgements

This project wouldn't be possible without some fair dinkum amazing open-source tech:

- **Models Used:** 
  - [Gemma 4:e2b](https://ai.google.dev/gemma) via Ollama (for fast local utilities and fallback)
  - [Groq](https://groq.com/) using `openai/gpt-oss-120b` for deep emotional reasoning
  - [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) for embeddings
- **Core Frameworks:** [Django](https://www.djangoproject.com/), [React](https://react.dev/), [Vite](https://vitejs.dev/)
- **AI Tooling:** [LangChain](https://langchain.com/) and [Ollama](https://ollama.com/)
- **Vector DB:** [Qdrant](https://qdrant.tech/)

## License

This project is licensed under the terms found in the `LICENSE` file. Have a squiz at it before you go deploying this everywhere.

---
*Stay safe, and remember: it's okay to not be okay.*
