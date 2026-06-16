# AI Ticket Platform

Enterprise-grade AI-powered ticket classification and Retrieval-Augmented Generation (RAG) SaaS platform built with FastAPI, Streamlit, PostgreSQL, Redis, Celery, and OpenAI.

---

# Features

* AI-powered ticket classification
* Retrieval-Augmented Generation (RAG)
* Enterprise document ingestion
* Semantic vector search
* Department auto-routing
* Streamlit frontend UI
* FastAPI backend APIs
* Background workers with Celery
* Multi-tenant ready architecture
* Structured logging
* Dockerized deployment
* ML classifier training pipeline
* Async PostgreSQL integration
* Modular enterprise architecture

---

# Technology Stack

## Backend

* Python 3.12+
* FastAPI
* SQLAlchemy
* PostgreSQL
* Redis
* Celery

---

## AI Stack

* OpenAI
* Sentence Transformers
* scikit-learn
* RAG pipeline
* Vector similarity search

---

## Frontend

* Streamlit

---

## Infrastructure

* Docker
* Docker Compose
* Makefile automation

---

# Project Structure

```text
ai-ticket-platform/
│
├── ai_ticket_platform/
│   ├── app/
│   │   ├── api/
│   │   ├── ai/
│   │   ├── models/
│   │   ├── services/
│   │   ├── utils/
│   │   ├── workers/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   └── security.py
│   │
│   ├── docs/
│   │   ├── ai_pipeline.md
│   │   ├── api.md
│   │   └── architecture.md
│   │
│   ├── frontend/
│   │   └── streamlit_app.py
│   │
│   ├── scripts/
│   │   ├── ingest_documents.py
│   │   ├── seed_data.py
│   │   └── train_classifier.py
│   │
│   └── tests/
│       ├── test_classifier.py
│       ├── test_rag.py
│       └── test_tickets.py
│
├── var/
│   ├── data/
│   │   ├── models/
│   │   ├── processed/
│   │   └── uploads/
│   │
│   └── log/
│
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── CHANGELOG.md
├── README.md
└── VERSION.txt
```

---

# Architecture Overview

```text
Frontend (Streamlit)
        │
        ▼
FastAPI REST API
        │
        ▼
Service Layer
        │
 ┌──────┼────────┐
 ▼      ▼        ▼
RAG   Ticket   Document
Svc    Svc      Svc
 │       │        │
 ▼       ▼        ▼
LLM   Classifier  Vector Store
 │
 ▼
OpenAI API
```

---

# Core AI Capabilities

## 1. Ticket Classification

The platform automatically predicts the correct support department:

* HR
* IT
* Transportation
* Finance
* Operations

using embeddings and machine learning classification.

---

## 2. Retrieval-Augmented Generation (RAG)

The platform supports enterprise semantic search:

1. Upload documents
2. Chunk documents
3. Generate embeddings
4. Store vectors
5. Retrieve context
6. Generate grounded AI responses

---

## 3. Vector Search

Semantic similarity search allows:

* enterprise knowledge retrieval
* contextual chatbot responses
* intelligent support automation

---

# Installation

## Clone Repository

```bash
git clone https://github.com/your-username/ai-ticket-platform.git

cd ai-ticket-platform
```

---

# Create Virtual Environment

## Linux / macOS

```bash
python3 -m venv .venv

source .venv/bin/activate
```

---

## Windows

```powershell
python -m venv .venv

.venv\Scripts\activate
```

---

# Install Dependencies

```bash
pip install --upgrade pip

pip install -e .
```

---

# Environment Variables

Create `.env` file:

```env
APP_NAME=AI Ticket Platform
APP_ENV=development
APP_DEBUG=true

API_HOST=0.0.0.0
API_PORT=8000

OPENAI_API_KEY=your_openai_api_key

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_ticket_platform

REDIS_URL=redis://localhost:6379/0

SECRET_KEY=change_me

VECTOR_STORE_BACKEND=inmemory
```

---

# Running Application

# Start FastAPI Backend

```bash
uvicorn ai_ticket_platform.app.main:app --reload
```

---

# Start Streamlit Frontend

```bash
streamlit run ai_ticket_platform/frontend/streamlit_app.py
```

---

# Start Celery Worker

```bash
celery -A ai_ticket_platform.app.workers.tasks worker --loglevel=info
```

---

# Docker Deployment

# Build Containers

```bash
docker compose build
```

---

# Start Platform

```bash
docker compose up
```

---

# API Documentation

After startup:

```text
Swagger UI:
http://localhost:8000/docs
```

```text
ReDoc:
http://localhost:8000/redoc
```

---

# Main API Endpoints

| Endpoint                      | Description      |
| ----------------------------- | ---------------- |
| GET /health                   | Health check     |
| POST /api/v1/chat/query       | AI RAG query     |
| POST /api/v1/tickets          | Create ticket    |
| GET /api/v1/tickets           | List tickets     |
| POST /api/v1/documents/upload | Upload documents |
| POST /api/v1/admin/reindex    | Reindex vectors  |

---

# AI Workflow

## Document Ingestion

```text
PDF/DOCX
   ↓
Chunking
   ↓
Embeddings
   ↓
Vector Index
```

---

## RAG Query Flow

```text
Question
   ↓
Embedding
   ↓
Similarity Search
   ↓
Context Retrieval
   ↓
OpenAI Completion
```

---

## Ticket Classification Flow

```text
User Ticket
    ↓
Embedding
    ↓
Classifier
    ↓
Department Prediction
```

---

# Logging

Structured logging is enabled across:

* APIs
* services
* AI operations
* workers
* vector retrieval
* database operations

Logs are stored in:

```text
var/log/
```

---

# Testing

Run all tests:

```bash
pytest
```

---

# Run Specific Tests

```bash
pytest ai_ticket_platform/tests/test_classifier.py
```

```bash
pytest ai_ticket_platform/tests/test_rag.py
```

```bash
pytest ai_ticket_platform/tests/test_tickets.py
```

---

# Development Commands

## Format Code

```bash
black .
```

---

## Run Linter

```bash
ruff check .
```

---

## Run Type Checks

```bash
mypy ai_ticket_platform
```

---

# Makefile Commands

```bash
make install
make run
make worker
make test
make lint
make format
make docker-up
make docker-down
```

---

# Security

Current security features:

* JWT utilities
* password hashing
* request validation
* upload validation
* tenant isolation

Planned:

* OAuth2
* RBAC
* SSO
* MFA

---

# Scalability

Designed for:

* horizontal API scaling
* distributed workers
* Kubernetes deployment
* enterprise SaaS workloads
* AI pipeline extensibility

---

# Future Roadmap

* pgvector support
* Pinecone integration
* LangChain agents
* multi-agent orchestration
* streaming responses
* OpenTelemetry tracing
* Prometheus monitoring
* Kubernetes deployment
* S3 document storage
* enterprise RBAC

---

# Documentation

Detailed documentation:

| File                 | Description         |
| -------------------- | ------------------- |
| docs/architecture.md | System architecture |
| docs/api.md          | API documentation   |
| docs/ai_pipeline.md  | AI pipeline details |

---

# License

MIT License

---

# Author

Valentin Sheboldaev

Senior Python Backend & AI Engineer

---

# Version

```text
1.0.0
```
