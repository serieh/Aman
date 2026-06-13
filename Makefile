.PHONY: dev dev-cloud up down frontend backend ollama logs clean

# ── Dev with Ollama fallback ─────────────────────────────────────────
dev:
	@echo "Starting development stack (with Ollama fallback)..."
	docker compose up -d
	ollama serve > /dev/null 2>&1 &
	$(MAKE) -j 2 backend-ollama frontend

# ── Dev cloud-only (no Ollama) ───────────────────────────────────────
dev-cloud:
	@echo "Starting development stack (cloud-only, no Ollama)..."
	docker compose up -d
	$(MAKE) -j 2 backend-cloud frontend

# ── Backend targets (internal) ───────────────────────────────────────
backend-ollama:
	@echo "Starting Backend (Ollama enabled)..."
	cd backend && uv sync && \
		AMAN_USE_OLLAMA=1 uv run python manage.py migrate && \
		AMAN_USE_OLLAMA=1 uv run daphne -b 127.0.0.1 -p 8000 core.asgi:application

backend-cloud:
	@echo "Starting Backend (cloud-only)..."
	cd backend && uv sync && \
		AMAN_USE_OLLAMA=0 uv run python manage.py migrate && \
		AMAN_USE_OLLAMA=0 uv run daphne -b 127.0.0.1 -p 8000 core.asgi:application

frontend:
	@echo "Starting Frontend..."
	cd frontend && npm install && NODE_OPTIONS="--no-warnings" npm run dev

ollama:
	@echo "Starting Ollama..."
	ollama serve

up:
	@echo "Starting Docker containers..."
	docker compose up -d

down:
	@echo "Stopping Docker containers..."
	docker compose down

clean: down
	@echo "Cleaning up processes and caches..."
	pkill -f "ollama serve" || true
	find . -type d -name "__pycache__" -exec rm -r {} + || true