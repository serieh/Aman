.PHONY: dev dev-test dev-ollama backend backend-ollama frontend up down showcase test

dev:
	@echo "Starting development stack (cloud-only, no Ollama)..."
	docker compose up -d
	$(MAKE) -j 2 backend frontend

dev-ollama:
	@echo "Starting development stack with Ollama enabled..."
	$(MAKE) up
	$(MAKE) -j 2 backend-ollama frontend

backend:
	@echo "Starting Backend (cloud-only)..."
	cd backend && uv sync && \
		AMAN_USE_OLLAMA=0 uv run python manage.py migrate && \
		AMAN_USE_OLLAMA=0 uv run daphne -b 127.0.0.1 -p 8000 core.asgi:application

backend-ollama:
	@echo "Starting Backend (Ollama enabled)..."
	cd backend && uv sync && \
		AMAN_USE_OLLAMA=1 uv run python manage.py migrate && \
		AMAN_USE_OLLAMA=1 uv run daphne -b 127.0.0.1 -p 8000 core.asgi:application

frontend:
	@echo "Starting Frontend..."
	cd frontend && npm install && NODE_OPTIONS="--no-warnings" npm run dev

up:
	@echo "Starting Docker containers and Ollama server..."
	docker compose up -d
	ollama serve > /dev/null 2>&1 &

down:
	@echo "Stopping Docker containers and Ollama server..."
	docker compose down
	pkill -f "ollama serve" || true

showcase:
	@echo "Starting Showcase stack..."
	cd showcase && npm install && npm run dev

test:
	@echo "Running tests..."
	uv run python Tests/run_tests.py --all