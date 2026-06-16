# API Documentation

## Overview

The AI Ticket Platform exposes a REST API built with FastAPI.

The API provides:

* Ticket management
* AI ticket classification
* RAG-based enterprise chat
* Document ingestion
* Knowledge-base retrieval
* Administrative tooling

---

# Base URL

```text
http://localhost:8000/api/v1
```

---

# Authentication

Current version:

```text
Development mode without enforced authentication
```

Planned:

* JWT Bearer authentication
* OAuth2
* RBAC
* Tenant-level authorization

---

# Content Type

All endpoints use:

```http
Content-Type: application/json
```

Except file uploads:

```http
multipart/form-data
```

---

# API Health

## Health Check

### Endpoint

```http
GET /health
```

### Description

Verify API availability.

---

### Response

```json
{
  "status": "ok",
  "service": "ai-ticket-platform"
}
```

---

# Tickets API

Base path:

```http
/api/v1/tickets
```

---

# Create Ticket

## Endpoint

```http
POST /tickets
```

---

## Description

Create support ticket with optional AI routing.

---

## Request Body

```json
{
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "created_by_user_id": "22222222-2222-2222-2222-222222222222",
  "title": "VPN access issue",
  "description": "VPN cannot connect after password reset.",
  "department": "it",
  "priority": "high"
}
```

---

## Fields

| Field              | Type   | Required | Description                 |
| ------------------ | ------ | -------- | --------------------------- |
| tenant_id          | UUID   | Yes      | Tenant identifier           |
| created_by_user_id | UUID   | No       | User identifier             |
| title              | string | Yes      | Ticket title                |
| description        | string | Yes      | Ticket body                 |
| department         | string | No       | Manual department override  |
| priority           | string | No       | low, medium, high, critical |

---

## Response

```json
{
  "id": "c2f4e5ab-3c9e-4b59-b9a4-4f42e9b56c19",
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "title": "VPN access issue",
  "description": "VPN cannot connect after password reset.",
  "department": "it",
  "priority": "high",
  "status": "open",
  "classification_confidence": 0.97
}
```

---

# Get Ticket

## Endpoint

```http
GET /tickets/{ticket_id}
```

---

## Query Parameters

| Parameter | Required | Description |
| --------- | -------- | ----------- |
| tenant_id | Yes      | Tenant UUID |

---

## Example

```http
GET /tickets/123?tenant_id=11111111-1111-1111-1111-111111111111
```

---

# List Tickets

## Endpoint

```http
GET /tickets
```

---

## Query Parameters

| Parameter     | Required | Description          |
| ------------- | -------- | -------------------- |
| tenant_id     | Yes      | Tenant UUID          |
| department    | No       | Filter by department |
| ticket_status | No       | Filter by status     |
| limit         | No       | Pagination limit     |
| offset        | No       | Pagination offset    |

---

## Example

```http
GET /tickets?tenant_id=11111111-1111-1111-1111-111111111111
```

---

# Update Ticket Status

## Endpoint

```http
PATCH /tickets/{ticket_id}/status
```

---

## Query Parameters

| Parameter | Required |
| --------- | -------- |
| tenant_id | Yes      |
| status    | Yes      |

---

## Example

```http
PATCH /tickets/123/status?tenant_id=11111111-1111-1111-1111-111111111111&status=resolved
```

---

# Add Ticket Message

## Endpoint

```http
POST /tickets/{ticket_id}/messages
```

---

## Request Body

```json
{
  "sender_type": "user",
  "content": "Additional issue details."
}
```

---

# Documents API

Base path:

```http
/api/v1/documents
```

---

# Upload Document

## Endpoint

```http
POST /documents/upload
```

---

## Content Type

```http
multipart/form-data
```

---

## Query Parameters

| Parameter  | Required |
| ---------- | -------- |
| tenant_id  | Yes      |
| department | No       |

---

## Form Fields

| Field | Type   | Required |
| ----- | ------ | -------- |
| file  | binary | Yes      |

---

## Supported File Types

* PDF
* DOCX
* TXT

---

## Example cURL

```bash
curl -X POST \
  "http://localhost:8000/api/v1/documents/upload?tenant_id=11111111-1111-1111-1111-111111111111" \
  -F "file=@vpn_policy.pdf"
```

---

## Response

```json
{
  "id": "2f6b8dcb-43f5-44c8-aee5-1d8e1c47b0b7",
  "filename": "vpn_policy.pdf",
  "department": "it",
  "chunk_count": 12,
  "is_processed": true
}
```

---

# Get Document

## Endpoint

```http
GET /documents/{document_id}
```

---

## Query Parameters

| Parameter | Required |
| --------- | -------- |
| tenant_id | Yes      |

---

# List Documents

## Endpoint

```http
GET /documents
```

---

## Query Parameters

| Parameter | Required |
| --------- | -------- |
| tenant_id | Yes      |
| limit     | No       |
| offset    | No       |

---

# Chat API

Base path:

```http
/api/v1/chat
```

---

# Ask AI Question

## Endpoint

```http
POST /chat/ask
```

---

## Description

Perform Retrieval-Augmented Generation using indexed documents.

---

## Request Body

```json
{
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "message": "How do I reset VPN access?",
  "top_k": 5
}
```

---

## Query Parameters

| Parameter  | Required |
| ---------- | -------- |
| department | No       |

---

## Response

```json
{
  "answer": "You must reset VPN passwords every 90 days.",
  "contexts": [
    {
      "document_id": "doc-1",
      "chunk_id": "chunk-1",
      "score": 0.95,
      "content": "Employees must reset VPN passwords every 90 days."
    }
  ]
}
```

---

# Admin API

Base path:

```http
/api/v1/admin
```

---

# Classify Raw Ticket Text

## Endpoint

```http
POST /admin/classify
```

---

## Query Parameters

| Parameter | Required |
| --------- | -------- |
| text      | Yes      |

---

## Example

```http
POST /admin/classify?text=VPN%20not%20working
```

---

## Response

```json
{
  "department": "it",
  "confidence": 0.96,
  "probabilities": {
    "it": 0.96,
    "hr": 0.01,
    "finance": 0.01
  }
}
```

---

# Admin Ticket Creation

## Endpoint

```http
POST /admin/tickets
```

---

# Admin Ticket Retrieval

## Endpoint

```http
GET /admin/tickets/{ticket_id}
```

---

# Admin Ticket Listing

## Endpoint

```http
GET /admin/tickets
```

---

# Response Codes

| Code | Meaning                   |
| ---- | ------------------------- |
| 200  | Success                   |
| 201  | Resource created          |
| 400  | Validation error          |
| 401  | Unauthorized              |
| 403  | Forbidden                 |
| 404  | Resource not found        |
| 422  | Request validation failed |
| 500  | Internal server error     |

---

# Error Response Format

```json
{
  "detail": "Ticket not found"
}
```

---

# Validation Rules

## Ticket Constraints

| Field       | Rule                                |
| ----------- | ----------------------------------- |
| title       | max 500 chars                       |
| description | max 10000 chars                     |
| priority    | low, medium, high, critical         |
| status      | open, in_progress, resolved, closed |

---

## File Upload Constraints

| Rule     | Value          |
| -------- | -------------- |
| Max Size | 25 MB          |
| Formats  | pdf, docx, txt |

---

# Pagination

Supported by listing endpoints.

## Parameters

| Parameter | Default |
| --------- | ------- |
| limit     | 50      |
| offset    | 0       |

---

# AI Features

## Automatic Classification

Powered by:

* embeddings
* scikit-learn classifier
* fallback keyword engine

---

## RAG Retrieval

Uses:

* vector similarity search
* cosine similarity
* semantic embeddings

---

## AI Summarization

Generates:

* executive summaries
* concise ticket descriptions
* escalation context

---

# Example End-to-End Workflow

## 1. Upload Knowledge Base

```http
POST /documents/upload
```

---

## 2. Create Ticket

```http
POST /tickets
```

---

## 3. Ask AI Question

```http
POST /chat/ask
```

---

# API Architecture

```text
Client
   ↓
FastAPI Router
   ↓
Service Layer
   ↓
AI Components
   ↓
Database / Vector Store
```

---

# Planned API Features

## Authentication

* JWT bearer auth
* OAuth2
* RBAC

---

## AI

* streaming responses
* agent workflows
* function calling
* tool execution

---

## Infrastructure

* WebSockets
* GraphQL
* gRPC
* OpenTelemetry
* Kafka integration

---

# Development URLs

| Service      | URL                         |
| ------------ | --------------------------- |
| API          | http://localhost:8000       |
| Swagger UI   | http://localhost:8000/docs  |
| ReDoc        | http://localhost:8000/redoc |
| Streamlit UI | http://localhost:8501       |

---

# Conclusion

The AI Ticket Platform API provides a modular enterprise-ready interface for:

* AI ticket automation
* semantic document search
* enterprise RAG workflows
* intelligent routing
* AI-powered support operations
