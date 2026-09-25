# e-Dossier LLM Technical Agent

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.11-1C3C3C.svg?style=flat)](https://www.langchain.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1.svg?style=flat&logo=postgresql)](https://github.com/pgvector/pgvector)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D.svg?style=flat&logo=redis)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?style=flat&logo=docker)](https://www.docker.com/)

An AI-powered Assistant and Retrieval-Augmented Generation (RAG) service designed for the **e-Dossier Student Information System (SIS)** and School Management Platform.

The **e-Dossier LLM Agent** integrates real-time school management data from the Go Backend API with knowledge base documentation (User Manual, System Architecture, and National Policy on Education) to provide intelligent responses, administrative actions, RAG document search, and real-time streaming chat.

---

## Key Features

- **Retrieval-Augmented Generation (RAG)**: Ingests and performs similarity search across system user manuals, architecture specifications, and policy documents stored in `pgvector`.
- **Real-Time Go Backend Integration**: Function-calling capabilities through LangChain tools to inspect state, LGA, school, student, personnel, and report data directly from the Go backend service.
- **Server-Sent Events (SSE) Streaming**: Low-latency `/chat/stream` endpoint for real-time text and tool streaming responses.
- **Persistent Chat Sessions**: Session history management powered by Redis with configurable TTL.
- **Document Processing & Chunking**: Automatic text extraction and chunking pipeline for PDF and text documents using `PyMuPDF` / `pypdf` and `langchain-text-splitters`.
- **Dockerized Architecture**: Complete multi-container orchestration with PostgreSQL (`pgvector`), Redis 7, and FastAPI.

---

## Architecture & System Overview

```
                          ┌───────────────────────────┐
                          │   Client Application /    │
                          │   e-Dossier SIS Frontend  │
                          └─────────────┬─────────────┘
                                        │ (HTTP / SSE)
                                        ▼
                          ┌───────────────────────────┐
                          │    FastAPI LLM Agent      │
                          │      (app/main.py)        │
                          └──────┬─────────────┬──────┘
                                 │             │
              ┌──────────────────┘             └──────────────────┐
              ▼                                                   ▼
┌───────────────────────────┐                       ┌───────────────────────────┐
│     LangChain Agent       │                       │   Document Processor &    │
│  (LLM: Llama 3.3 / GPT-4) │                       │      Vector Store     │
└─────────────┬─────────────┘                       └─────────────┬─────────────┘
              │                                                   │
      ┌───────┴───────┐                                           │
      ▼               ▼                                           ▼
┌───────────┐   ┌───────────┐                       ┌───────────────────────────┐
│  Redis    │   │Go Backend │                       │   PostgreSQL + pgvector   │
│ (Session  │   │ API Tools │                       │   (document_embeddings)   │
│  History) │   └─────┬─────┘                       └───────────────────────────┘
└───────────┘         │
                      ▼
        ┌───────────────────────────┐
        │     Go Backend Service    │
        │  (http://localhost:34006) │
        └───────────────────────────┘
```

---

## Project Structure

```
edossiertechagent/
├── app/
│   ├── main.py                   # FastAPI application initialization & lifespan handler
│   ├── api/
│   │   └── routes.py             # REST API routes (Chat, Streaming, Documents, Health)
│   ├── core/
│   │   └── config.py             # Pydantic Settings & Environment variables configuration
│   ├── models/
│   │   ├── chat.py               # Pydantic models for chat requests, responses & sessions
│   │   └── document.py           # Document ingestion & chunk data models
│   ├── services/
│   │   ├── llm_agent.py          # Core LangChain Agent logic & RAG execution pipeline
│   │   ├── vector_store.py       # Async pgvector interface for similarity search & persistence
│   │   └── document_processor.py  # File parser (PDF/TXT) and text chunker service
│   └── tools/
│       ├── go_backend.py         # Async HTTP client for Go Backend API endpoints
│       └── langchain_tools.py    # LangChain BaseTool wrappers for LLM function calling
├── data/                         # Local database mount / persistent files
├── documents/                    # Knowledge base source documents
├── Dockerfile                    # Container definition for FastAPI agent
├── docker-compose.yml            # Multi-service setup (Postgres + pgvector, Redis, LLM Agent)
├── extract_pdf.py                # Standalone script for PDF extraction and testing
├── init-vector-db.sql            # PostgreSQL vector & uuid extension initialization script
└── requirements.txt              # Python dependencies
```

---

## Prerequisites

- **Python**: `3.11` or higher
- **Docker & Docker Compose** (for containerized setup)
- **PostgreSQL**: Version 16 with the `pgvector` extension
- **Redis**: Version 7+

---

## Environment Variables

Create a `.env` file in the root directory:

```env
# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Database Configuration (PostgreSQL + pgvector)
DATABASE_URL=postgresql+asyncpg://edossier:secret@localhost:5433/edossier

# Redis Session Store
REDIS_URL=redis://localhost:6380/0

# LLM & Embedding Provider (OpenRouter / OpenAI compatible)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.3-70b-instruct
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Go Backend Integration
GO_BACKEND_URL=http://localhost:34006
GO_BACKEND_TIMEOUT=30
ML_RECOMMENDER_URL=http://localhost:9001

# Security
JWT_SECRET=your_jwt_secret_here
```

---

## Getting Started

### 1. Running with Docker Compose (Recommended)

To start the full stack including PostgreSQL (`pgvector`), Redis, and the LLM Agent:

```bash
docker-compose up --build
```

The services will be available at:
- **FastAPI LLM Agent**: `http://localhost:8000`
- **Swagger API Docs**: `http://localhost:8000/docs`
- **PostgreSQL Database**: `localhost:5433`
- **Redis Cache**: `localhost:6380`

### 2. Manual Local Setup

1. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure PostgreSQL & Redis are running**:
   - Create PostgreSQL database `edossier` and enable `pgvector`:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     CREATE EXTENSION IF NOT EXISTS pg_trgm;
     CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
     ```

4. **Start the FastAPI application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## Key API Endpoints

### System Health
- **`GET /api/v1/health`**: Checks connectivity to PostgreSQL, `pgvector`, and the Go Backend API.

### Chat & Streaming
- **`POST /api/v1/chat`**: Send a message to the agent.
  ```json
  {
    "message": "List all schools in Lagos state",
    "session_id": "optional-session-id",
    "use_rag": true,
    "use_tools": true
  }
  ```
- **`POST /api/v1/chat/stream`**: Stream chat responses in real-time via Server-Sent Events (SSE).

### Document Ingestion & RAG
- **`POST /api/v1/documents/ingest`**: Process and chunk files in `./documents` into `pgvector`.
- **`GET /api/v1/documents`**: List ingested documents in the vector store.
- **`GET /api/v1/vector-store/stats`**: Retrieve database embedding metrics.

### Session Management
- **`POST /api/v1/sessions`**: Create a new user chat session.
- **`GET /api/v1/sessions/{session_id}`**: Retrieve session message statistics and history.
- **`DELETE /api/v1/sessions/{session_id}`**: Clear session history from Redis.

---

## License

This project is proprietary and confidential property of the e-Dossier Platform team.
