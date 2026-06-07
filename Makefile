.PHONY: dev up down frontend backend ollama logs clean

dev:
	@echo "Starting the entire development stack..."
	docker compose up -d                  
	ollama serve > /dev/null 2>&1 &       
	$(MAKE) -j 2 backend frontend         

frontend:
	@echo "Starting Frontend..."
	cd frontend && npm install && NODE_OPTIONS="--no-warnings" npm run dev

backend:
	@echo "Starting Backend..."
	cd backend && uv sync && uv run python manage.py migrate && uv run python manage.py runserver

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