# How to Run Aman Reformed

This guide outlines the steps to spin up the entire Aman AI project locally.

## Prerequisites

Ensure you have the following installed on your machine:
- **Docker** and **Docker Compose**
- **Node.js** (v18+) and **npm**
- **Python** (v3.10+) and **uv** (fast Python package installer)
- **Ollama** (Running locally)

---

## 1. Start the Databases (Docker)

Aman relies on PostgreSQL for relational data and Qdrant for vector storage (RAG and long-term memory).

```bash
docker compose up -d
```
*This starts the `aman_postgres` and `aman_qdrant` containers in the background.*

---

## 2. Start the Local AI Models (Ollama)

Ensure Ollama is running in the background. The system relies on two local fallback/fast models:

```bash
ollama run gemma4:26b
ollama run gemma4:e2b
```
*(Note: As of v6.1, the primary thinking model is offloaded to Groq, but the local models act as fast summarization/fallback engines).*

---

## 3. Run the Backend (Django)

Open a new terminal window.

```bash
cd backend

# Install dependencies using uv
uv sync

# Run database migrations (if this is the first time)
uv run python manage.py migrate

# Start the Django/Daphne server (usually runs on port 8000)
uv run python manage.py runserver
```

---

## 4. Run the Frontend (React + Vite)

Open another new terminal window.

```bash
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```

The frontend will typically be available at `http://localhost:5173`. 
Open this URL in your browser to access the landing page and chat dashboard.
