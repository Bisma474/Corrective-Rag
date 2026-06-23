# Corrective RAG (CRAG) Platform

> **A production-grade implementation of the CRAG paper** — *Corrective Retrieval-Augmented Generation* (Yan et al., 2024)

Built live at: [correctiverag.vercel.app](https://correctiverag.vercel.app)

---

## The Problem

Standard RAG systems retrieve document chunks and feed them to an LLM. But when the retrieved documents are **irrelevant** or the knowledge base **lacks an answer**, these systems either **hallucinate** or produce misleading responses. This is a critical failure mode for any QA system.

## The CRAG Solution (From the Paper)

The paper ["Corrective Retrieval-Augmented Generation"](https://arxiv.org/abs/2401.15884) by Yan et al. (2024) proposed an elegant fix: add a **corrective evaluator** between retrieval and generation that:

1. **Grades** each retrieved passage for relevance
2. **Decides** a path:
   - **Correct** (relevant) → Generate from local documents
   - **Incorrect** (irrelevant) → Rewrite query → Web search → Generate from web results
3. **Synthesizes** the final answer with source citations

This transforms RAG from a passive pipeline into an **agentic system** with fallback reasoning.

---

## What I Changed From the Paper

| Paper's Approach | My Implementation | Rationale |
|---|---|---|
| Trained evaluator (T5-based) | Cosine similarity threshold (0.18) | No training data needed; works zero-shot |
| Google Search API (paid) | DuckDuckGo HTML scraper | Free, no API key required |
| Single LLM (ChatGPT) | Groq (llama-3.3-70b) + heuristic fallback | Free tier, low latency, reliable |
| Command-line tool | Full-stack web app (React + FastAPI) | Real-world usable product |
| Batch processing | Real-time logging of each pipeline step | Transparency & debugging |

The core CRAG idea — **evaluate-then-decide** with web fallback — is preserved, but adapted for a production web environment.

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────┐
│  1. RETRIEVAL               │
│  Vector DB search (FAISS)   │
│  Filtered by user's docs    │
└──────────┬──────────────────┘
           │ 5 candidate chunks
           ▼
┌─────────────────────────────┐
│  2. EVALUATION              │
│  Cosine similarity scoring  │
│  Threshold: 0.18            │
└──────────┬──────────────────┘
           │
           ▼
    ┌──────┴──────┐
    │             │
  PASS          FAIL
  (≥0.18)       (<0.18)
    │             │
    │             ▼
    │    ┌──────────────────┐
    │    │ 3. QUERY REWRITE │
    │    │ Strip filler words│
    │    └────────┬─────────┘
    │             │
    │             ▼
    │    ┌──────────────────┐
    │    │ 4. WEB SEARCH    │
    │    │ DuckDuckGo (4    │
    │    │ results)         │
    │    └────────┬─────────┘
    │             │
    └──────┬──────┘
           │ context chunks
           ▼
┌─────────────────────────────┐
│  5. GENERATION              │
│  Groq → Gemini → OpenAI     │
│  → Heuristic fallback       │
│  + Source citations         │
└──────────┬──────────────────┘
           │
           ▼
    Final Answer + Pipeline Logs
```

---

## Features

- **Multi-format upload**: PDF, TXT, Markdown → chunked (500 chars, 100 overlap) → embedded (all-MiniLM-L6-v2)
- **Multi-tenant isolation**: Users only see their own documents at database and vector search level
- **Real-time pipeline logs**: Toggle-able drawer showing each CRAG step with live messages
- **Groq LLM**: llama-3.3-70b-versatile via Groq API (with heuristic fallback)
- **Conversation memory**: Multi-turn chat with previous context preserved
- **JWT auth**: Register/login with bcrypt + 24h tokens
- **Dark glassmorphism UI**: Premium obsidian design, mobile-responsive

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite 8 + react-markdown |
| Backend | FastAPI + Uvicorn |
| Vector Store | Custom FAISS (numpy-based, persisted via pickle) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Database | SQLite |
| Auth | JWT + bcrypt |
| Container | Docker (multi-stage) + Docker Compose |
| Deployment | Vercel (frontend) + Railway (backend) |

---

## Quick Start

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (another terminal)
cd frontend
npm install
npm run dev
```

Set your API keys in `backend/.env`:
```env
JWT_SECRET=your-secret-key
GROQ_API_KEY=gsk_...
```

---

## Live Demo

- **Frontend**: [correctiverag.vercel.app](https://correctiverag.vercel.app)
- **API Docs**: [celebrated-adaptation-production-95fd.up.railway.app/docs](https://celebrated-adaptation-production-95fd.up.railway.app/docs)

---

## Why This Matters for AI Engineering

This project demonstrates:
- **Agentic AI design patterns** — evaluation loops, conditional branching, fallback strategies
- **Understanding of retrieval theory** — chunking strategies, embedding similarity, multi-tenant search
- **LLM orchestration** — working with multiple providers, prompt engineering, failover handling
- **Full-stack product engineering** — from paper concept to deployed web application
- **Performance awareness** — eliminating redundant computation (100% speedup on query evaluation)
