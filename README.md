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

Forget typing out twenty different commands. We've got a `Makefile` that does the heavy lifting for you. Open up a few terminal tabs and let 'er rip:

### 1. Start the Databases
```bash
make up
```
*(This fires up PostgreSQL and Qdrant via Docker.)*

### 2. Start the AI Models
```bash
make ollama
```
*(Ensure Ollama is running first! This will load the local models we need.)*

### 3. Start the Backend
```bash
make backend
```
*(This syncs your Python dependencies using `uv`, runs migrations, and starts the Django server.)*

### 4. Start the Frontend
```bash
make frontend
```
*(Installs node modules and spins up the Vite dev server.)*

Once that's all humming along, point your browser to `http://localhost:5173` and say hello to Aman!

## Credits & Acknowledgements

This project wouldn't be possible without some fair dinkum amazing open-source tech:

- **Models Used:** 
  - [Gemma 4:26b](https://ai.google.dev/gemma) & [Gemma 4:e2b](https://ai.google.dev/gemma) via Ollama
  - [Groq](https://groq.com/) using `openai/gpt-oss-120b` for the heavy thinking
  - [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) for embeddings
- **Core Frameworks:** [Django](https://www.djangoproject.com/), [React](https://react.dev/), [Vite](https://vitejs.dev/)
- **AI Tooling:** [LangChain](https://langchain.com/) and [Ollama](https://ollama.com/)
- **Vector DB:** [Qdrant](https://qdrant.tech/)

## License

This project is licensed under the terms found in the `LICENSE` file. Have a squiz at it before you go deploying this everywhere.

---
*Stay safe, and remember: it's okay to not be okay.*
