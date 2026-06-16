# AI Pipeline Documentation

## Overview

The AI Ticket Platform uses a multi-stage AI pipeline for:

* Automatic ticket classification
* Document ingestion and indexing
* Retrieval-Augmented Generation (RAG)
* Semantic search
* AI-powered ticket summarization
* Knowledge-base question answering

The platform follows an enterprise-grade modular AI architecture with separated responsibilities between ingestion, embeddings, retrieval, reasoning, and orchestration layers.

---

# High-Level Architecture

```text
                     ┌────────────────────┐
                     │   User / Client    │
                     └─────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ FastAPI Endpoints   │
                    └─────────┬───────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
 ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
 │ Ticket Service │  │ Document Svc   │  │ Chat / RAG Svc │
 └────────┬───────┘  └────────┬───────┘  └────────┬───────┘
          │                   │                   │
          ▼                   ▼                   ▼
 ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
 │ Classifier     │  │ Chunking       │  │ Vector Search  │
 │ Service        │  │ Service        │  │ + Retrieval     │
 └────────┬───────┘  └────────┬───────┘  └────────┬───────┘
          │                   │                   │
          ▼                   ▼                   ▼
 ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
 │ Embeddings     │  │ Embeddings     │  │ LLM Generation │
 │ Generation     │  │ Generation     │  │                │
 └────────────────┘  └────────────────┘  └────────────────┘
```

---

# Core AI Components

## 1. Embedding Pipeline

### Purpose

Convert text into dense vector embeddings for:

* Semantic search
* Ticket similarity
* RAG retrieval
* Context matching
* Knowledge-base indexing

### File

```text
app/ai/embeddings.py
```

### Current Provider

OpenAI Embeddings API

### Default Model

```text
text-embedding-3-small
```

### Flow

```text
Input Text
    ↓
Normalize Text
    ↓
OpenAI Embedding API
    ↓
Dense Float Vector
    ↓
Store in Vector DB
```

### Example

```python
embedding = embedding_provider.embed_text(
    "VPN access is not working"
)
```

---

# 2. Document Ingestion Pipeline

## Purpose

Transform enterprise documents into searchable AI knowledge.

### Supported Formats

* PDF
* DOCX
* TXT

### File

```text
app/services/document_service.py
```

---

## Pipeline Flow

```text
Document Upload
      ↓
File Validation
      ↓
Text Extraction
      ↓
Chunking
      ↓
Embedding Generation
      ↓
Vector Store Indexing
      ↓
Metadata Persistence
```

---

## Step Details

### 1. Validation

Checks:

* Extension whitelist
* File size
* Tenant ownership
* Upload integrity

### 2. Text Extraction

Extraction methods:

| Type | Parser        |
| ---- | ------------- |
| PDF  | pypdf         |
| DOCX | python-docx   |
| TXT  | native reader |

### 3. Chunking

Implemented in:

```text
app/ai/chunking.py
```

Default configuration:

```env
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

Purpose:

* Preserve semantic continuity
* Improve retrieval quality
* Reduce hallucinations

### 4. Embeddings

Each chunk becomes:

```python
VectorDocument(
    content="...",
    embedding=[...],
    metadata={...},
)
```

### 5. Vector Indexing

Indexed into:

```text
InMemoryVectorStore
```

Future support planned:

* pgvector
* Pinecone
* Qdrant
* Weaviate

---

# 3. Ticket Classification Pipeline

## Purpose

Automatically route tickets to departments.

### File

```text
app/services/classifier_service.py
```

---

## Classification Flow

```text
Ticket Text
     ↓
Embedding Generation
     ↓
ML Classifier
     ↓
Department Prediction
     ↓
Confidence Score
```

---

## Current Model

```text
LogisticRegression
```

Using:

```python
scikit-learn
```

---

## Departments

Supported departments:

* IT
* HR
* Finance
* Legal
* Security
* Transportation

---

## Fallback Strategy

If trained model is unavailable:

```text
Keyword-based classification
```

Example:

```python
"vpn", "laptop", "network"
→ IT
```

---

# 4. RAG Pipeline

## Purpose

Provide grounded AI answers using enterprise documents.

### File

```text
app/services/rag_service.py
```

---

# RAG Flow

```text
User Question
      ↓
Embedding Generation
      ↓
Vector Similarity Search
      ↓
Top-K Relevant Chunks
      ↓
Context Assembly
      ↓
LLM Prompt Generation
      ↓
OpenAI Completion
      ↓
Grounded AI Answer
```

---

# Retrieval Phase

## Vector Search

Current implementation:

```text
InMemoryVectorStore
```

Search algorithm:

```text
Cosine Similarity
```

Filtering support:

* tenant_id
* department
* metadata

---

## Example

```python
results = vector_store.search(
    query_embedding=embedding,
    top_k=5,
    filters={
        "tenant_id": "...",
        "department": "it",
    },
)
```

---

# Context Building

Retrieved chunks become:

```text
[Context 1]
Document: vpn_policy.txt
Department: it
Score: 0.95

Content:
Reset VPN password every 90 days.
```

---

# 5. LLM Generation Pipeline

## Purpose

Generate AI reasoning and responses.

### File

```text
app/services/llm_service.py
```

---

# Current Provider

OpenAI Chat Completions API

### Default Model

```text
gpt-4o-mini
```

---

# Supported AI Operations

## Ticket Summarization

```text
Long Ticket
     ↓
LLM
     ↓
Executive Summary
```

---

## Escalation Analysis

Detect:

* urgency
* emotional tone
* risk
* severity

---

## RAG Answers

Grounded answers using retrieved context.

---

## LLM Classification

Optional alternative to ML classifier.

---

# Prompt System

## File

```text
app/ai/prompts.py
```

---

# Prompt Types

| Prompt                       | Purpose                |
| ---------------------------- | ---------------------- |
| rag_qa_prompt                | RAG question answering |
| ticket_classification_prompt | Department prediction  |
| ticket_summarization_prompt  | Ticket summaries       |
| escalation_analysis_prompt   | Escalation risk        |

---

# Example Prompt Structure

```text
System Prompt
    +
User Context
    +
Retrieved Chunks
    ↓
LLM Completion
```

---

# 6. Evaluation Pipeline

## File

```text
app/ai/evaluation.py
```

---

# Metrics

## Classification Metrics

* accuracy
* precision
* recall
* F1 score

---

## Retrieval Metrics

* similarity score
* top-k relevance
* retrieval coverage

---

## RAG Metrics

* groundedness
* hallucination rate
* answer relevance

---

# 7. Background Workers

## File

```text
app/workers/tasks.py
```

---

# Celery Tasks

| Task                  | Purpose              |
| --------------------- | -------------------- |
| classify_ticket_task  | Async classification |
| summarize_ticket_task | AI summarization     |
| reindex_document_task | Vector refresh       |
| health_check_task     | Worker validation    |

---

# Async Processing Flow

```text
API Request
    ↓
Celery Queue
    ↓
Background Worker
    ↓
AI Processing
    ↓
Database Update
```

---

# 8. Multi-Tenant AI Isolation

## Tenant Separation

Every AI object contains:

```text
tenant_id
```

Isolation enforced in:

* vector retrieval
* ticket retrieval
* document indexing
* chat queries

---

# Example

```python
filters = {
    "tenant_id": str(tenant_id),
}
```

---

# 9. Security Pipeline

## Security Features

* JWT authentication
* Password hashing
* Tenant isolation
* Upload validation
* Request validation
* Input normalization

---

# 10. Observability

## Structured Logging

Every AI stage logs:

* event
* operation
* status
* timing
* metadata
* errors

---

# Example Log

```json
{
  "event": "rag_context_retrieval_completed",
  "operation": "retrieve_contexts",
  "status": "success",
  "context_count": 5
}
```

---

# 11. Current AI Limitations

## Current Constraints

* In-memory vector store
* No reranking
* No streaming responses
* No hybrid retrieval
* Single embedding provider
* No fine-tuned classifier yet

---

# 12. Planned AI Improvements

## Retrieval

* pgvector
* hybrid BM25 + vector search
* semantic reranking
* metadata boosting

---

## LLM

* streaming responses
* tool calling
* agent workflows
* function calling

---

## Classification

* transformer classifiers
* fine-tuning
* active learning
* feedback loops

---

## Infrastructure

* distributed vector DB
* Kubernetes deployment
* autoscaling workers
* GPU inference

---

# 13. End-to-End Example

## Ticket Creation

```text
User submits ticket
      ↓
TicketService
      ↓
ClassifierService
      ↓
Embedding Generation
      ↓
ML Prediction
      ↓
Department Assignment
      ↓
Ticket Stored
      ↓
Optional AI Summary
```

---

## Document Chat

```text
User asks question
      ↓
RAGService
      ↓
Embedding Generation
      ↓
Vector Search
      ↓
Top-K Chunks
      ↓
LLM Prompt
      ↓
Grounded AI Response
```

---

# Conclusion

The AI Ticket Platform implements a modular enterprise AI architecture designed for:

* scalability
* maintainability
* observability
* multi-tenancy
* extensibility
* production AI workflows

The current implementation provides a strong foundation for evolving into:

* enterprise helpdesk AI
* agentic support platform
* internal enterprise copilot
* autonomous ticket-routing system
* AI operations platform
