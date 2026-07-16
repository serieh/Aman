# Setup and Deployment

## Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **Docker & Docker Compose** (for PostgreSQL and Qdrant)
- **uv** (recommended for Python package management)

## Environment Configuration

Copy the `.env.example` file to create your local `.env`:
```bash
cp .env.example .env
```
Ensure you provide the following critical variables:
- `GROQ_API_KEY`: Required for LLM inference.
- `POSTGRES_URL` (or `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).
- `QDRANT_HOST` and `QDRANT_PORT`.
- `SECRET_KEY`: A secure random string for Django.

## Running the Application

A `Makefile` is provided to simplify operations.

### Local Development (Cloud LLM)
To start the databases via Docker, run database migrations, and spawn the backend and frontend dev servers concurrently:
```bash
make dev-cloud
```

### Local Development (With Ollama Fallback)
If you wish to run local models (e.g., Gemma 4:e2b) for fast utilities:
```bash
make dev
```

### Manual Startup (Separate Terminals)
If you prefer running services independently:
1. **Databases**: `make up`
2. **Django Backend**: `cd Backend && uv run python manage.py runserver 0.0.0.0:8000`
3. **FastAPI AI Service**: `cd Backend && PYTHONPATH=agent uv run uvicorn service.api.main:app --reload --port 8001`
4. **React Frontend**: `cd Frontend && npm run dev`

## Production Build

To build the React frontend for production:
```bash
cd Frontend
npm run build
npm run preview
```
The Django backend should be served using a production ASGI server like Daphne or Uvicorn behind a reverse proxy (e.g., Nginx) to manage WebSocket connections securely.
