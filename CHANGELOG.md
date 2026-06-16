# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog
and this project follows Semantic Versioning.

---

# [0.1.1] - 2026-06-16

## Fixed

* Fixed API router registration for health, documents, tickets, chat, and admin endpoints.
* Fixed incorrect `api` package path issue caused by a leading space in the folder name.
* Fixed reserved Python logging fields by replacing unsafe `filename` usage with `document_filename`.
* Fixed document upload flow by validating tenant existence and database table initialization.
* Fixed PostgreSQL Docker port conflict by supporting isolated local Docker database usage.
* Fixed Celery startup by using the explicit Celery app path.
* Fixed missing `sentence-transformers` dependency for local embedding support.

## Added

* Added working document upload and indexing flow through Streamlit and FastAPI.
* Added demo tenant and demo user setup requirements for local development.
* Added database initialization support using SQLAlchemy metadata.
* Added clearer local infrastructure setup for PostgreSQL and Redis.

## Changed

* Improved local development workflow for backend, frontend, Celery, Redis, and PostgreSQL.
* Improved error diagnosis for upload, ticket creation, and RAG retrieval flows.
* Confirmed current vector store limitation: in-memory vectors are lost after backend restart.

## Known Limitations

* Vector search currently uses in-memory storage and is not persistent across backend restarts.
* Persistent vector storage with PostgreSQL pgvector is planned for the next minor release.

# [0.1.0] - 2026-06-16

## Added

### Core Platform

* Initial enterprise AI SaaS platform architecture
* FastAPI backend with async support
* Streamlit frontend dashboard
* Multi-tenant support
* Structured service-oriented architecture
* Environment-based configuration management
* Centralized structured logging system
* Custom exception hierarchy
* Security utilities and JWT token support

### AI Features

* AI-powered ticket classification
* RAG (Retrieval-Augmented Generation) support
* OpenAI integration
* Embedding generation support
* Prompt template registry
* Evaluation utilities for retrieval and classification
* Ticket summarization support
* Escalation analysis support

### Vector Search

* In-memory vector database implementation
* Cosine similarity search
* Document chunk indexing
* Metadata filtering
* Vector document builders
* Embedding provider abstraction

### Document Processing

* PDF text extraction
* DOCX text extraction
* TXT text extraction
* Text chunking with overlap support
* Automatic embedding generation
* Knowledge-base document ingestion
* Vector indexing pipeline

### Ticket System

* Ticket creation and routing
* AI department prediction
* Ticket messaging support
* Ticket lifecycle management
* Ticket priority management
* Ticket status updates
* AI-generated ticket summaries

### API

* Health endpoints
* Ticket API
* Admin API
* Chat API
* Document API
* Validation using Pydantic models
* Async SQLAlchemy integration

### Database

* Async PostgreSQL support
* SQLAlchemy ORM models
* Tenant models
* User models
* Ticket models
* Document models
* Chunk models

### Workers

* Celery background task integration
* Ticket summarization task
* Document reindex task
* Health-check task

### Frontend

* Streamlit dashboard
* Ticket management UI
* AI chat interface
* Document upload interface
* Admin tooling
* API health verification

### Scripts

* Document ingestion script
* Database seed script
* Classifier training script

### Testing

* Ticket service tests
* RAG tests
* Classifier tests
* Validation tests
* Vector store tests

### DevOps

* `.env.example`
* Docker-ready structure
* Celery integration
* Redis integration
* Logging directories
* Model storage directories

---

# Planned

## Upcoming Features

* PostgreSQL pgvector integration
* Hybrid search
* Semantic reranking
* OAuth2 authentication
* Role-based access control
* Kubernetes deployment manifests
* CI/CD pipelines
* LangChain integration
* Observability dashboards
* Prometheus metrics
* Grafana dashboards
* S3 document storage
* WebSocket support
* Streaming AI responses
* OpenTelemetry tracing
* Kafka event streaming
* AI feedback loop training
* Fine-tuned classifiers
* Agentic workflow orchestration
* Full React frontend
* Elasticsearch support
* Qdrant integration
* Pinecone integration
* Audit logging
* Multi-region deployment support
