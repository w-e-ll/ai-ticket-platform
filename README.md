# AI Ticket Platform

Enterprise-grade AI-powered ticket classification and Retrieval-Augmented Generation (RAG) SaaS platform built with FastAPI, Streamlit, PostgreSQL, Redis, Celery, and OpenAI.

---

## Screenshots

### Upload Knowledge Base Documents

![Upload Documents](ai_ticket_platform/docs/upload.png)

### Create AI Support Tickets

![Create Ticket](ai_ticket_platform/docs/create.png)

### Admin Panel

![Admin Panel](ai_ticket_platform/docs/admin.png)

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
* Multi-tenant architecture
* Structured JSON logging
* Async PostgreSQL support
* Redis integration
* ML classifier training pipeline
* Dockerized infrastructure
* Modular enterprise architecture

---

# Current Status

## Working Features

* Ticket creation
* AI classification
* Document upload and indexing
* RAG pipeline
* OpenAI embeddings
* Streamlit frontend
* PostgreSQL persistence
* Celery workers
* Redis queue integration
* Multi-tenant support

---

## Current Limitation

The current vector store implementation uses:

```text
InMemoryVectorStore
```

This means:

* embeddings are NOT persisted
* vectors are lost after backend restart
* RAG search only works during active runtime session

Planned upgrade:

```text
PostgreSQL pgvector integration
```

---

# Technology Stack

## Backend

* Python 3.12+
* FastAPI
* SQLAlchemy Async ORM
* PostgreSQL
* Redis
* Celery

---

## AI Stack

* OpenAI
* Sentence Transformers
* scikit-learn
* RAG pipeline
* Embedding generation
* Semantic similarity search

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
│   │   ├── ai/
│   │   │   ├── chunking.py
│   │   │   ├── embeddings.py
│   │   │   ├── evaluation.py
│   │   │   ├── prompts.py
│   │   │   └── vector_store.py
│   │   │
│   │   ├── api/
│   │   │   ├── admin.py
│   │   │   ├── chat.py
│   │   │   ├── documents.py
│   │   │   ├── health.py
│   │   │   └── tickets.py
│   │   │
│   │   ├── models/
│   │   │   ├── db.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── services/
│   │   │   ├── classifier_service.py
│   │   │   ├── document_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── rag_service.py
│   │   │   └── ticket_service.py
│   │   │
│   │   ├── workers/
│   │   │   └── tasks.py
│   │   │
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   └── security.py
│   │
│   ├── docs/
│   ├── frontend/
│   ├── scripts/
│   └── tests/
│
├── uploads/
├── logs/
├── var/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── CHANGELOG.md
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

Create `.env`

```env
APP_NAME=AI Ticket Platform
APP_ENV=development
APP_DEBUG=true

API_HOST=0.0.0.0
API_PORT=8000

OPENAI_API_KEY=your_openai_api_key

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/ai_ticket_platform

REDIS_URL=redis://localhost:6379/0

SECRET_KEY=change_me

VECTOR_STORE_BACKEND=inmemory
```

---

# Infrastructure Startup

## Start Redis

If Redis container already exists:

```bash
docker start ai-ticket-redis
```

Or create new:

```bash
docker-compose up -d redis
```

---

## Start PostgreSQL

Recommended Docker port:

```text
5433
```

because local Ubuntu PostgreSQL often already occupies:

```text
5432
```

Start container:

```bash
docker-compose up -d postgres
```

---

# Initialize Database

Connect:

```bash
psql -h localhost -p 5433 -U postgres -d ai_ticket_platform
```

---

## Create Demo Tenant

```sql
INSERT INTO tenants (id, name, is_active)
VALUES (
    '11111111-1111-1111-1111-111111111112',
    'Demo Tenant',
    true
);
```

---

## Create Demo User

```sql
INSERT INTO users (
    id,
    tenant_id,
    email,
    full_name,
    hashed_password,
    role,
    is_active
)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111112',
    'demo.user@example.com',
    'Demo User',
    'demo_password_hash',
    'admin',
    true
);
```

---

# Run Backend

```bash
uvicorn ai_ticket_platform.app.main:app --reload
```

Swagger:

```text
http://localhost:8000/docs
```

---

# Run Frontend

```bash
streamlit run ai_ticket_platform/frontend/streamlit_app.py
```

Frontend:

```text
http://localhost:8501
```

---

# Run Celery Worker

Correct startup command:

```bash
celery -A ai_ticket_platform.app.workers.tasks.celery_app worker --loglevel=info
```

---

# Main API Endpoints

| Endpoint                      | Description      |
| ----------------------------- | ---------------- |
| GET /health                   | Health check     |
| POST /api/v1/chat/ask         | AI RAG query     |
| POST /api/v1/tickets          | Create ticket    |
| GET /api/v1/tickets           | List tickets     |
| POST /api/v1/documents/upload | Upload documents |
| POST /api/v1/admin/reindex    | Reindex vectors  |

---

# Working Local Flow

## 1. Upload Documents

Upload:

* PDF
* DOCX
* TXT

through Streamlit UI.

---

## 2. Documents Are Processed

Pipeline:

```text
Document
  ↓
Chunking
  ↓
Embedding Generation
  ↓
InMemoryVectorStore
```

---

## 3. Ask AI Questions

Questions are answered using:

```text
semantic similarity + retrieved context + OpenAI
```

---

# Logging

Structured logging enabled for:

* API requests
* AI operations
* vector search
* database operations
* Celery workers
* RAG retrieval

Logs stored in:

```text
logs/
```

---

# Testing

Run all tests:

```bash
pytest
```

---

# Development Commands

## Format

```bash
black .
```

---

## Lint

```bash
ruff check .
```

---

## Type Checking

```bash
mypy ai_ticket_platform
```

---

# Docker Commands

## Build

```bash
docker compose build
```

---

## Start

```bash
docker compose up
```

---

## Stop

```bash
docker compose down
```

---

# Troubleshooting

## Redis Connection Refused

Start Redis:

```bash
docker start ai-ticket-redis
```

---

## PostgreSQL Port Already Used

Check:

```bash
sudo lsof -i :5432
```

Use Docker PostgreSQL on:

```text
5433
```

Update `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/ai_ticket_platform
```

---

## RAG Returns No Context

Current limitation:

```text
InMemoryVectorStore resets after backend restart
```

Re-upload documents after restart.

Planned fix:

```text
pgvector persistent vector storage
```

---

# Future Roadmap

* pgvector support
* Persistent vector storage
* Hybrid search
* Pinecone integration
* LangChain agents
* Streaming responses
* Kubernetes deployment
* OpenTelemetry tracing
* Prometheus monitoring
* S3 document storage
* Enterprise RBAC

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
0.1.1
```
