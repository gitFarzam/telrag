# TelRAG Project Evaluation — AI Engineer Recruitment Assessment

> **Evaluator Perspective:** Technical recruitment for AI Engineer with RAG deployment expertise  
> **Project:** TelRAG — Telegram-integrated Retrieval-Augmented Generation Chatbot  
> **Date:** April 2026

---

## Executive Summary

TelRAG is a **production-grade RAG application** built with Django, PostgreSQL (pgvector), and Celery. It combines real-time WebSocket chat with Telegram bot integration, featuring a hybrid search pipeline (semantic + keyword), async document ingestion, and LLM-powered response generation. The project demonstrates solid engineering practices but has notable gaps for a modern AI engineering role.

| Aspect | Rating | Notes |
|--------|--------|-------|
| **RAG Implementation** | ⭐⭐⭐⭐☆ | Solid core, hybrid search |
| **ML/AI Integration** | ⭐⭐⭐☆☆ | Basic, limited experimentation |
| **DevOps/Deployment** | ⭐⭐⭐⭐☆ | Docker-ready, monitoring included |
| **Code Quality** | ⭐⭐⭐⭐☆ | Well-structured Django app |
| **Scalability** | ⭐⭐⭐☆☆ | Missing caching, rate limiting |

---

## 1. Technology Stack

### 1.1 Core Technologies

| Category | Technology | Version | Assessment |
|----------|------------|---------|------------|
| **Web Framework** | Django | 5.2.13 | ✅ Modern, stable |
| **ASGI Server** | Daphne | 4.2.1 | ✅ Required for Channels |
| **WebSocket** | Django Channels | 4.3.2 | ✅ Real-time capable |
| **Language** | Python | 3.12 | ✅ Current |
| **Database** | PostgreSQL | 16 | ✅ With pgvector |
| **Vector Store** | pgvector | 0.4.2 | ✅ Native vector ops |
| **Message Broker** | Redis | 7 | ✅ Celery backend |
| **Task Queue** | Celery | 5.6.2 | ✅ Async processing |

### 1.2 AI/ML Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| `openai` | 2.26.0 | LLM (GPT-4.1-mini) for response generation & categorization |
| `huggingface_hub` | 1.6.0 | Embedding model (sentence-transformers/all-MiniLM-L6-v2) |
| `langchain-core` | 1.2.9 | RAG orchestration (minimal usage) |
| `langchain-text-splitters` | 1.1.0 | Text chunking |

### 1.3 Supporting Stack

| Tool | Purpose |
|------|---------|
| `flower` | Celery monitoring UI (port 5555) |
| `django-prometheus` | Prometheus metrics export |
| `Grafana Alloy` | Log aggregation |
| `python-dotenv` | Environment configuration |

---

## 2. RAG Pipeline Analysis

### 2.1 Document Ingestion Flow

```
Telegram/Web Upload → Content Extraction → Chunking → Embedding → Vector Storage
```

**Implementation Details:**

| Stage | Technology | Config |
|-------|------------|--------|
| **Chunking** | LangChain `RecursiveCharacterTextSplitter` | 4000 tokens chunk, 200 overlap |
| **Embedding** | HuggingFace `all-MiniLM-L6-v2` | 384-dimensional vectors |
| **Vector Storage** | pgvector in PostgreSQL | L2 distance metric |

**Pros:**
- ✅ Proper chunking with overlap for context preservation
- ✅ Conversation-scoped retrieval (isolates documents per conversation)
- ✅ Supports multiple content types: text, audio (Whisper transcription), images (caption metadata)

**Cons:**
- ❌ No chunking strategy alternatives (fixed 4000-token)
- ❌ No evaluation framework for retrieval quality
- ❌ No explicit re-ranking layer

### 2.2 Query Processing Pipeline

```
User Query → Category Classification → Hybrid Search → Context Assembly → LLM Response
```

**Category Classification (OpenAI):**
- **Category 0:** Question fully answerable with context
- **Category 1:** General question (no context needed)
- **Category 2:** Context insufficient
- **Category 3:** Out of scope

**Hybrid Search Implementation:**
- **Semantic Search:** Vector similarity via pgvector (`L2Distance`)
- **Keyword Search:** PostgreSQL full-text search (`SearchVector`, `SearchRank`)
- **Combined Ranking:** `-rank` (keyword) + `distance` (semantic)

**Pros:**
- ✅ Hybrid approach is production-ready best practice
- ✅ Category classification adds guardrails
- ✅ Top-5 retrieval provides sufficient context

**Cons:**
- ❌ Hardcoded top-5 retrieval (no adaptive retrieval)
- ❌ No query rewriting or expansion
- ❌ No hybrid fusion algorithm (simple linear combination)

---

## 3. Architecture & Project Structure

### 3.1 Service Architecture (Docker Compose)

```
┌─────────────────────────────────────────────────────────────────┐
│                        telrag-network                             │
├──────────┬──────────┬──────────┬──────────┬──────────┬────────┤
│   db     │  redis   │   app    │  celery  │celery_beat│ flower │
│(pgvector)│   (7)    │ (Daphne) │ (worker) │ (scheduler)│(UI)   │
│  :5432   │  :6379   │ :8006    │  (async) │  (10min)  │ :5555 │
└──────────┴──────────┴──────────┴──────────┴──────────┴────────┘
```

### 3.2 Key Source Files

| File | Responsibility |
|------|-----------------|
| `src/chat/services.py` | Core RAG pipeline (ingestion, hybrid search) |
| `src/chat/utils/rag.py` | `NLPToolKit`, `RetrievalToolKit` |
| `src/chat/consumers.py` | WebSocket consumer (`ChatConsumer`) |
| `src/chat/operations.py` | Telegram message processor |
| `src/chat/tasks.py` | Celery tasks (`task_new_message`, `task_reply_message`) |
| `src/django_project/settings.py` | Full configuration |

**Pros:**
- ✅ Clear separation of concerns
- ✅ Async task processing for heavy operations
- ✅ WebSocket real-time delivery

**Cons:**
- ❌ No API layer (REST/GraphQL) — only Django views
- ❌ No service layer abstraction (直接业务逻辑 in views)
- ❌ Limited test coverage (`src/chat/tests.py` exists but content unknown)

---

## 4. Deployment & DevOps

### 4.1 Containerized Services

| Service | Image | Ports | Purpose |
|---------|-------|-------|---------|
| `db` | pgvector/pgvector:pg16 | 5432 | Vector-enabled PostgreSQL |
| `redis` | redis:7 | 6379 | Celery broker + cache |
| `app` | Custom Dockerfile | 8006 | Daphne ASGI server |
| `celery` | Custom | — | Async workers |
| `celery_beat` | Custom | — | Scheduled tasks |
| `flower` | Custom | 5555 | Celery monitoring |

### 4.2 Observability

| Component | Tool | Endpoint |
|-----------|------|----------|
| **Metrics** | django-prometheus | `http://app:8006/metrics` |
| **Logs** | Grafana Alloy | JSON aggregation |
| **Task Monitoring** | Flower | `http://localhost:5555` |

**Pros:**
- ✅ Production-ready Docker Compose setup
- ✅ Prometheus metrics endpoint
- ✅ Celery monitoring via Flower
- ✅ Environment-based configuration (`.env`)

**Cons:**
- ❌ No health check endpoints (`/health`)
- ❌ No container orchestration (Kubernetes readiness)
- ❌ No CI/CD pipeline defined
- ❌ No secrets management (plain `.env`)

---

## 5. Strengths (What an AI Engineer Would Like)

### 5.1 Technical Strengths

1. **pgvector Integration** — Native vector operations in PostgreSQL, avoiding external vector DB complexity
2. **Hybrid Search** — Combining semantic + keyword search demonstrates understanding of retrieval trade-offs
3. **Async Processing** — Celery tasks for document ingestion prevents blocking
4. **Multi-channel Support** — Web + Telegram unified interface
5. **Category Guardrails** — LLM-based query classification before retrieval

### 5.2 Code Organization

- Clear Django app structure (`models.py`, `views.py`, `services.py`, `tasks.py`)
- Separation of RAG utilities in `src/chat/utils/rag.py`
- Configuration via `constants.py` and environment variables

### 5.3 Production Readiness

- Docker Compose for local development
- Prometheus metrics scraping
- Scheduled cleanup tasks (`task_delete_unused_conversation`)
- Demo mode toggle (`DEMO=True`)

---

## 6. Gaps & Missing Components

### 6.1 RAG-Specific Gaps

| Missing | Impact | Recommendation |
|---------|--------|----------------|
| **Vector DB alternatives** | No comparison with Weaviate/Qdrant/Milvus | Add Weaviate or Qdrant for evaluation |
| **Evaluation framework** | No RAGAs, retrieval precision metrics | Integrate `ragas` or custom metrics |
| **Query expansion** | Limited semantic matching | Add query rewriting |
| **Re-ranking** | No cross-encoder reranking | Integrate `sentence-transformers` reranker |
| **Cache layer** | Repeated embeddings for same queries | Add Redis caching for embeddings |

### 6.2 AI/ML Gaps

| Missing | Impact | Recommendation |
|---------|--------|----------------|
| **LLM flexibility** | Hardcoded to OpenAI | Add Anthropic, local LLM options |
| **Fine-tuning** | No fine-tuned embeddings | Evaluate domain-specific models |
| **Prompt management** | Inline prompts in `prompts.py` | Use LangChain prompt templates |
| **A/B testing** | No experimentation framework | Add prompt versioning |

### 6.3 Infrastructure Gaps

| Missing | Impact | Recommendation |
|---------|--------|----------------|
| **API layer** | No REST/GraphQL for external clients | Add DRF or FastAPI gateway |
| **Rate limiting** | No protection against abuse | Add Django ratelimit or Redis limiter |
| **Caching** | No Redis caching for queries | Add embedding + response cache |
| **Secrets management** | Plain `.env` files | Integrate HashiCorp Vault |
| **Load balancing** | Single app instance | Add Traefik or nginx |

### 6.4 Developer Experience Gaps

| Missing | Impact | Recommendation |
|---------|--------|----------------|
| **Type hints** | Limited typing | Add full type annotations |
| **Testing** | No visible test suite | Add pytest + coverage |
| **Documentation** | Basic README | Add API docs, architecture diagram |
| **Linting** | No ruff/flake8 config | Add pre-commit hooks |

---

## 7. Interview Questions for AI Engineer Candidate

### 7.1 RAG Fundamentals

1. **How would you improve the hybrid search algorithm?**  
   *Expected:* Discuss late interaction, learned sparse representations, hybrid fusion weights

2. **What evaluation metrics would you add for retrieval quality?**  
   *Expected:* Recall@K, MRR, NDCG, or RAGAs framework

3. **How would you handle scaling from 100 to 100,000 documents?**  
   *Expected:* Discuss vector DB partitioning, approximate nearest neighbors, sharding

### 7.2 System Design

4. **Why pgvector instead of dedicated vector databases?**  
   *Expected:* Trade-offs discussion — simplicity vs. specialized features

5. **How would you add a re-ranking layer?**  
   *Expected:* Cross-encoder integration, bi-encoder vs. cross-encoder comparison

6. **Design a cache layer for repeated queries.**  
   *Expected:* Redis caching of embeddings + LLM responses, cache invalidation strategy

### 7.3 Deployment

7. **How would you containerize for Kubernetes?**  
   *Expected:* K8s manifests, horizontal pod autoscaling, readiness probes

8. **What's missing for production hardening?**  
   *Expected:* Rate limiting, secrets management, health checks, logging standardization

---

## 8. Overall Assessment

### Candidate Strengths Demonstrated by This Project

| Skill | Evidence |
|-------|----------|
| ✅ **RAG implementation** | Hybrid search, chunking, embedding pipeline |
| ✅ **Async processing** | Celery tasks for heavy operations |
| ✅ **Real-time systems** | Django Channels + WebSocket |
| ✅ **Containerization** | Docker Compose multi-service setup |
| ✅ **Observability** | Prometheus + Grafana Alloy |
| ✅ **Database design** | PostgreSQL + pgvector schema |

### Areas for Candidate Growth

| Skill | Gap |
|-------|-----|
| ❌ **Vector DB diversity** | Only pgvector — no exposure to Weaviate/Qdrant |
| ❌ **RAG evaluation** | No metrics or benchmarking |
| ❌ **LLM flexibility** | Single provider (OpenAI) |
| ❌ **API design** | No REST/GraphQL experience |
| ❌ **Advanced caching** | No Redis for query caching |
| ❌ **Infrastructure as Code** | No Terraform/Ansible |

---

## 9. Conclusion

**Verdict:** This project is a **solid mid-level RAG application** suitable for a junior-to-mid AI Engineer. It demonstrates practical experience with:

- End-to-end RAG pipeline (ingestion → retrieval → generation)
- Hybrid search implementation
- Async task processing
- Containerized deployment
- Real-time WebSocket communication

**Recommended Role Fit:**  
- **Junior AI Engineer** — Strong match  
- **Mid-level AI Engineer** — Partial match (gaps in evaluation, caching, multi-vector DB)  
- **Senior AI Engineer** — Below expectations (missing advanced patterns)

**Next Steps for Candidate:**  
1. Add RAG evaluation framework (RAGAs)
2. Experiment with alternative vector databases
3. Implement Redis caching layer
4. Add REST API layer with FastAPI
5. Write comprehensive test suite

---

> *Evaluation conducted as part of technical recruitment assessment for AI Engineer position specializing in RAG application deployment.*