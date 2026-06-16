PYTHON=python
PIP=pip
PYTEST=pytest
UVICORN=uvicorn

APP_MODULE=ai_ticket_platform.app.main:app

DOCKER_COMPOSE=docker compose

.DEFAULT_GOAL := help


help:
	@echo ""
	@echo "AI Ticket Platform Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install            Install dependencies"
	@echo "  make run                Run FastAPI server"
	@echo "  make frontend           Run Streamlit frontend"
	@echo "  make worker             Run Celery worker"
	@echo ""
	@echo "Database:"
	@echo "  make seed               Seed demo data"
	@echo ""
	@echo "AI:"
	@echo "  make train              Train classifier"
	@echo "  make ingest             Ingest documents"
	@echo ""
	@echo "Testing:"
	@echo "  make test               Run tests"
	@echo "  make test-verbose       Run tests verbose"
	@echo ""
	@echo "Formatting:"
	@echo "  make format             Run black"
	@echo "  make lint               Run ruff"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up          Start containers"
	@echo "  make docker-down        Stop containers"
	@echo "  make docker-logs        View logs"
	@echo "  make docker-build       Build containers"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean              Remove caches"
	@echo ""


install:
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e .


run:
	$(UVICORN) $(APP_MODULE) --host 0.0.0.0 --port 8000 --reload


frontend:
	streamlit run ai_ticket_platform/frontend/streamlit_app.py


worker:
	celery -A ai_ticket_platform.app.workers.tasks.celery_app worker --loglevel=INFO


seed:
	$(PYTHON) -m ai_ticket_platform.scripts.seed_data


train:
	$(PYTHON) -m ai_ticket_platform.scripts.train_classifier \
		--dataset data/training/tickets.csv \
		--save-model


ingest:
	$(PYTHON) -m ai_ticket_platform.scripts.ingest_documents \
		--tenant-id 11111111-1111-1111-1111-111111111111 \
		--path data/documents


test:
	$(PYTEST) ai_ticket_platform/tests -q


test-verbose:
	$(PYTEST) ai_ticket_platform/tests -vv


format:
	black ai_ticket_platform


lint:
	ruff check ai_ticket_platform


docker-up:
	$(DOCKER_COMPOSE) up -d


docker-down:
	$(DOCKER_COMPOSE) down


docker-logs:
	$(DOCKER_COMPOSE) logs -f


docker-build:
	$(DOCKER_COMPOSE) build


clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
