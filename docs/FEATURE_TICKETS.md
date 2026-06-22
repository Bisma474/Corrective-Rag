# Feature Ticket List

## Ticket Template

### Ticket ID
FEAT-001

### Feature Name
### Priority
- Must-Have / Should-Have / Nice-to-Have
### Objective
### Detailed Requirements
### Acceptance Criteria
- User can...
- System should...
- API returns...
### Dependencies
### Technical Notes
- Files
- Endpoints
- DB changes
### Testing Requirements
- Unit tests
- Integration tests
- Manual tests

### AI Coding Prompt
Generate a ready-to-use prompt for Cursor/Claude/Codex.

---

## EPICS & TICKETS

### EPIC 1: Project Setup

#### FEAT-101: Project Directory Structure and Virtual Environment
- **Priority**: Must-Have
- **Objective**: Establish development environments for FastAPI (backend) and React-Vite (frontend).
- **Acceptance Criteria**:
  - `backend/` runs locally with `requirements.txt` dependencies.
  - `frontend/` runs with `npm run dev`.
- **AI Coding Prompt**:
  `Create a boilerplate structure for FastAPI backend in backend/ and Vite React in frontend/ with basic files and config.`

---

### EPIC 2: Authentication

#### FEAT-201: JWT User Auth Router
- **Priority**: Should-Have
- **Objective**: Implement login and register endpoints with secure token generation.
- **Acceptance Criteria**:
  - `/api/auth/register` creates hashed user record in SQLite.
  - `/api/auth/login` yields JWT token.
- **AI Coding Prompt**:
  `Implement SQLite user auth database scheme and login/register FastAPI routers using bcrypt and pyjwt.`

---

### EPIC 3: Core Features

#### FEAT-301: Document Ingestion and Vector Store
- **Priority**: Must-Have
- **Objective**: Extract text from PDF/TXT uploads, compute embeddings, and store in vector database index.
- **Acceptance Criteria**:
  - File uploaded via `/api/documents/upload` is chunked and saved to index.
- **AI Coding Prompt**:
  `Create a Python class in backend/app/services/document_service.py to ingest, chunk, and embed documents using FAISS or a lightweight local index.`

#### FEAT-302: Corrective Retrieval-Augmented Generation Agent
- **Priority**: Must-Have
- **Objective**: Core CRAG routing: retrieve local context -> grade relevance -> fallback to DuckDuckGo search if grade fails -> output text.
- **Acceptance Criteria**:
  - Query checks local DB. If relevance score is low, triggers web fallback.
- **AI Coding Prompt**:
  `Implement a CRAG pipeline service. Create a document relevance evaluator and a web search service that queries DuckDuckGo if relevance is below a threshold.`

---

### EPIC 4: Frontend UI

#### FEAT-401: Glassmorphic Main Interface & Chat UI
- **Priority**: Must-Have
- **Objective**: Build the dashboard containing the chat message list, prompt text field, file dropzone, and side panel showing past conversations.
- **Acceptance Criteria**:
  - Custom styled components with dark obsidian gradients and glassmorphism.
- **AI Coding Prompt**:
  `Build a React chat interface with custom CSS module, incorporating a sleek dark palette, modern typography, source citations, and SSE message streaming support.`

---

### EPIC 5: Security

#### FEAT-501: Rate Limiter and Input Sanitizer
- **Priority**: Must-Have
- **Objective**: Prevent query abuse and malicious inputs.
- **Acceptance Criteria**:
  - FastAPI blocks queries after exceeding rate limits.
- **AI Coding Prompt**:
  `Configure CORSMiddleware in FastAPI and implement basic rate limiting for the chat query endpoint.`

---

### EPIC 6: Observability

#### FEAT-601: Agent Pipeline Log Viewer
- **Priority**: Must-Have
- **Objective**: Stream detailed pipeline logs to the UI indicating execution steps.
- **Acceptance Criteria**:
  - Right panel displays live status: "Retrieving..." -> "Evaluating..." -> "Web Search Triggered" -> "Generating...".
- **AI Coding Prompt**:
  `Stream CRAG agent pipeline execution logs using Server-Sent Events alongside LLM answer text, displaying them visually in the React frontend.`

---

### EPIC 7: Deployment

#### FEAT-701: Unified Deployment Setup
- **Priority**: Should-Have
- **Objective**: Ready the workspace to deploy in a containerized environment.
- **Acceptance Criteria**:
  - A Dockerfile compiles both frontend and backend for deployment.
- **AI Coding Prompt**:
  `Create a Dockerfile to build and package frontend assets, run them via backend server static file host, or running them concurrently.`
