# Architecture Documentation

# AI Ticket Platform

## Overview

AI Ticket Platform is an enterprise-grade AI SaaS application for:

* automatic ticket classification
* semantic knowledge-base search
* Retrieval-Augmented Generation (RAG)
* intelligent support automation
* enterprise document ingestion
* AI-powered ticket workflows

The platform follows a modular service-oriented architecture designed for:

* scalability
* observability
* maintainability
* multi-tenancy
* AI extensibility

---

# High-Level Architecture

```text id="bn4r8k"
                         ┌────────────────────┐
                         │     Frontend       │
                         │    Streamlit UI    │
                         └─────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │      FastAPI        │
                        │    REST Gateway     │
                        └─────────┬───────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
┌────────────────┐     ┌────────────────┐      ┌────────────────┐
│ Ticket Service │     │ Document Svc   │      │ RAG Service    │
└────────┬───────┘     └────────┬───────┘      └────────┬───────┘
         │                      │                       │
         ▼                      ▼                       ▼
┌────────────────┐     ┌────────────────┐      ┌────────────────┐
│ Classifier     │     │ Chunking       │      │ Vector Store   │
│ Service        │     │ Pipeline       │      │ Retrieval      │
└────────┬───────┘     └────────┬───────┘      └────────┬───────┘
         │                      │                       │
         ▼                      ▼                       ▼
┌────────────────┐     ┌────────────────┐      ┌────────────────┐
│ Embeddings     │     │ Embeddings     │      │ OpenAI LLM     │
│ Provider       │     │ Indexing       │      │ Generation     │
└────────────────┘     └────────────────┘      └────────────────┘
```

---

# System Components

# 1. API Layer

## Technology

```text id="3d8d4m"
FastAPI
```

---

## Responsibilities

* HTTP request handling
* request validation
* routing
* response serialization
* dependency injection
* authentication integration
* OpenAPI documentation

---

## API Modules

| Module       | Purpose                |
| ------------ | ---------------------- |
| health.py    | Health monitoring      |
| tickets.py   | Ticket management      |
| documents.py | Document ingestion     |
| chat.py      | RAG interactions       |
| admin.py     | Administrative tooling |

---

# 2. Service Layer

## Purpose

Encapsulates business logic and orchestration.

---

# Ticket Service

## File

```text id="7l5tgo"
app/services/ticket_service.py
```

---

## Responsibilities

* ticket creation
* routing orchestration
* status transitions
* AI summary generation
* message management

---

# Document Service

## File

```text id="7a59e2"
app/services/document_service.py
```

---

## Responsibilities

* file validation
* document extraction
* chunking
* embedding generation
* vector indexing

---

# RAG Service

## File

```text id="fd4zjp"
app/services/rag_service.py
```

---

## Responsibilities

* semantic retrieval
* context assembly
* prompt preparation
* grounded response generation

---

# Classifier Service

## File

```text id="fw3jwb"
app/services/classifier_service.py
```

---

## Responsibilities

* department prediction
* ML model loading
* fallback classification
* classifier training

---

# LLM Service

## File

```text id="ehgmyq"
app/services/llm_service.py
```

---

## Responsibilities

* OpenAI integration
* prompt execution
* summarization
* escalation analysis
* RAG completion

---

# 3. AI Layer

## Purpose

Provides machine learning and LLM functionality.

---

# Embeddings

## File

```text id="kijisr"
app/ai/embeddings.py
```

---

## Responsibilities

* embedding generation
* provider abstraction
* vector normalization

---

## Current Provider

```text id="zjlwmk"
OpenAI Embeddings API
```

---

# Chunking

## File

```text id="ztmx0f"
app/ai/chunking.py
```

---

## Responsibilities

* semantic chunk splitting
* overlap preservation
* retrieval optimization

---

# Vector Store

## File

```text id="gx47ci"
app/ai/vector_store.py
```

---

## Responsibilities

* vector indexing
* similarity search
* metadata filtering
* retrieval scoring

---

## Current Implementation

```text id="n7om5r"
InMemoryVectorStore
```

---

## Planned Backends

* pgvector
* Pinecone
* Qdrant
* Weaviate

---

# Prompts

## File

```text id="2l5fba"
app/ai/prompts.py
```

---

## Responsibilities

* centralized prompt registry
* prompt rendering
* template management

---

# Evaluation

## File

```text id="tv77te"
app/ai/evaluation.py
```

---

## Responsibilities

* retrieval metrics
* classification scoring
* AI evaluation utilities

---

# 4. Persistence Layer

# Database

## Technology

```text id="j18r9r"
PostgreSQL
```

---

## ORM

```text id="0mijbl"
SQLAlchemy Async ORM
```

---

# Database Models

## File

```text id="7qgkhm"
app/models/db.py
```

---

## Entities

| Entity        | Purpose                |
| ------------- | ---------------------- |
| Tenant        | Multi-tenant isolation |
| User          | User accounts          |
| Ticket        | Support tickets        |
| TicketMessage | Ticket conversations   |
| Document      | Uploaded files         |
| DocumentChunk | Indexed chunks         |

---

# Multi-Tenancy

All entities include:

```text id="dcbxwq"
tenant_id
```

Isolation enforced at:

* retrieval
* indexing
* querying
* routing

---

# 5. Vector Search Architecture

# Current Design

```text id="n4oboo"
Application Memory
    ↓
Python Vector Store
    ↓
Cosine Similarity
```

---

# Retrieval Flow

```text id="1ewl94"
Question
   ↓
Embedding
   ↓
Vector Search
   ↓
Top-K Chunks
   ↓
LLM Context
```

---

# Similarity Algorithm

```text id="0s31c7"
Cosine Similarity
```

---

# Metadata Filtering

Supported filters:

* tenant_id
* department
* document_id

---

# 6. Background Processing

# Technology

```text id="j5jrl4"
Celery + Redis
```

---

# Worker Tasks

## File

```text id="6zpvz9"
app/workers/tasks.py
```

---

## Tasks

| Task                  | Purpose              |
| --------------------- | -------------------- |
| classify_ticket_task  | Async classification |
| summarize_ticket_task | AI summarization     |
| reindex_document_task | Vector refresh       |
| health_check_task     | Worker monitoring    |

---

# Async Workflow

```text id="x3lmnl"
API Request
    ↓
Redis Queue
    ↓
Celery Worker
    ↓
AI Processing
    ↓
Database Update
```

---

# 7. Frontend Architecture

# Technology

```text id="9thqvp"
Streamlit
```

---

# Frontend Features

| Feature     | Description        |
| ----------- | ------------------ |
| AI Chat     | RAG interaction    |
| Ticket UI   | Ticket management  |
| Upload UI   | Document ingestion |
| Admin Tools | AI diagnostics     |

---

# Frontend File

```text id="kp3o8r"
frontend/streamlit_app.py
```

---

# 8. Security Architecture

# Current Features

* JWT utilities
* password hashing
* input validation
* upload validation
* tenant isolation

---

# Security Module

## File

```text id="17n5lf"
app/security.py
```

---

# Planned Security

* OAuth2
* RBAC
* SSO
* MFA
* audit logging

---

# 9. Logging & Observability

# Logging Architecture

## File

```text id="t26im7"
app/utils/logging.py
```

---

# Features

* structured logging
* per-module loggers
* JSON-compatible metadata
* centralized formatting

---

# Log Metadata

| Field          | Purpose             |
| -------------- | ------------------- |
| event          | Event name          |
| operation      | Business operation  |
| status         | success/failure     |
| tenant_id      | Tenant traceability |
| exception_type | Error analysis      |

---

# Example

```json id="0o3rnq"
{
  "event": "ticket_creation_completed",
  "operation": "create_ticket",
  "status": "success",
  "ticket_id": "123"
}
```

---

# 10. Configuration Management

# File

```text id="vtdr4m"
app/config.py
```

---

# Configuration Sources

* environment variables
* .env file
* runtime overrides

---

# Managed Settings

* database
* OpenAI
* Redis
* Celery
* vector store
* chunking
* uploads
* logging

---

# 11. Deployment Architecture

# Docker Compose

## Services

| Service  | Purpose             |
| -------- | ------------------- |
| api      | FastAPI application |
| worker   | Celery workers      |
| postgres | Relational database |
| redis    | Queue backend       |
| frontend | Streamlit UI        |

---

# Deployment Flow

```text id="h85n4t"
Docker Compose
     ↓
Container Network
     ↓
Microservice Communication
```

---

# 12. AI Pipeline Architecture

# Ticket Classification

```text id="qq6buh"
Ticket
   ↓
Embedding
   ↓
ML Classifier
   ↓
Department Prediction
```

---

# Document Ingestion

```text id="1gkxw6"
Document
   ↓
Extraction
   ↓
Chunking
   ↓
Embeddings
   ↓
Vector Index
```

---

# RAG Flow

```text id="swt7l5"
Question
   ↓
Embedding
   ↓
Similarity Search
   ↓
Context Assembly
   ↓
LLM Completion
```

---

# 13. Scalability Design

# Horizontal Scalability

Supports scaling:

* API containers
* Celery workers
* vector search backends
* Redis queues

---

# Stateless APIs

FastAPI layer is stateless.

Allows:

* Kubernetes deployment
* load balancing
* autoscaling

---

# Future Scalability

Planned:

* distributed vector DB
* GPU inference
* async streaming
* Kafka event bus

---

# 14. Testing Architecture

# Test Types

| Type             | Coverage      |
| ---------------- | ------------- |
| Unit tests       | Services      |
| Validation tests | Inputs        |
| Vector tests     | Retrieval     |
| RAG tests        | Context logic |
| Classifier tests | ML behavior   |

---

# Test Framework

```text id="10mr2o"
pytest
```

---

# 15. Error Handling

# Centralized Exceptions

## File

```text id="qjlwm7"
app/utils/errors.py
```

---

# Error Types

| Exception            | Purpose         |
| -------------------- | --------------- |
| TicketCreationError  | Ticket failures |
| ClassificationError  | ML failures     |
| RetrievalError       | RAG failures    |
| VectorStoreError     | Vector failures |
| DocumentParsingError | Parsing issues  |

---

# 16. Planned Architecture Evolution

# AI

* hybrid retrieval
* semantic reranking
* agent workflows
* multi-agent orchestration
* tool calling

---

# Infrastructure

* Kubernetes
* Helm charts
* CI/CD pipelines
* OpenTelemetry
* Prometheus

---

# Storage

* pgvector
* S3 document storage
* distributed embeddings cache

---

# Security

* enterprise RBAC
* SSO
* audit trails
* encryption at rest

---

# 17. Architectural Principles

# Core Principles

## Modularity

Each AI capability is isolated into services.

---

## Separation of Concerns

API, AI, persistence, and orchestration are separated.

---

## Observability

Every operation produces structured logs.

---

## Extensibility

Providers and vector stores are abstracted.

---

## Multi-Tenancy

Tenant isolation enforced at every layer.

---

## AI-First Design

Architecture optimized for future AI expansion.

---

# Conclusion

The AI Ticket Platform architecture provides a strong enterprise foundation for:

* AI support systems
* intelligent ticket routing
* enterprise knowledge retrieval
* semantic search
* autonomous support workflows
* future agentic AI systems

The modular architecture enables rapid scaling toward:

* enterprise copilots
* AI operations platforms
* autonomous service desks
* intelligent workflow orchestration
