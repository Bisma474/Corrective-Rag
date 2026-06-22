# Product Requirements Document (PRD)

## 1. Product Overview
### What the app does
**Corrective Retrieval-Augmented Generation (CRAG) Platform** is an enterprise-grade AI system that ensures factual correctness in QA systems. It ingests documents, indexes them into a vector database, and uses an agentic retrieval pipeline. When queried, it:
1. Retrieves candidate document passages.
2. Grades the relevance of retrieved documents using a evaluator model.
3. Automatically triggers an external web search (e.g., Tavily or DuckDuckGo) as a fallback if the retrieved documents are insufficient or ambiguous.
4. Rewrites/optimizes the search query before fetching web results.
5. Synthesizes the final response with clear citations, separating local document sources and web search results.

### Vision and mission
To eliminate hallucinations in business QA systems, providing users with absolute certainty that every answer is grounded in factual document sources or validated web search data.

---

## 2. Target Users
- **Knowledge Workers / Analysts**: Need to search internal documents accurately.
- **Developers / System Architects**: Need a verifiable RAG system that tells them exactly *why* a source was chosen, and when web fallback was triggered.

---

## 3. Problem Statement
Standard RAG pipelines retrieve document chunks blindly and feed them to the LLM. If the retrieval is inaccurate, or the database does not contain the answer, the LLM hallucinates or gives a confidently wrong response. Existing solutions lack an automated "corrective" layer that evaluates source quality on-the-fly and pulls in live web search data to fill knowledge gaps.

---

## 4. Goals and Success Metrics
### Business Goals
- Build a lightweight, easily deployable CRAG system that runs locally or in the cloud.
- Provide a beautiful, highly interactive frontend that builds trust through step-by-step transparency.

### Success Metrics
- **Accuracy**: >95% accurate answering based on local doc context.
- **Zero Hallucination rate**: Automatic fallback to web search when document relevance is low, rather than answering with empty or wrong context.
- **UX Delight**: Real-time visualization of the CRAG execution path (Grader -> Search -> Synthesizer).

---

## 5. Core Features
| Feature | Description | Priority |
|---|---|---|
| **Document Upload** | Support for PDF, TXT, and Markdown files. | Must-Have |
| **CRAG Search & Chat** | Interactive QA chat interface with step-by-step agent logs. | Must-Have |
| **Pipeline Visualizer** | A UI module showing if documents were "Correct", "Incorrect", or "Ambiguous" and if web search was triggered. | Must-Have |
| **Source Citation** | Explicitly showing local file citations or web links used for the answer. | Must-Have |
| **User Authentication** | Basic secure JWT authentication. | Should-Have |

---

## 6. User Journey
1. **User logs in** and is greeted by a modern dark-themed dashboard.
2. **User uploads a document** (e.g., a company policy document).
3. **User submits a query** (e.g., "What is our company's remote work policy?").
4. **Pipeline executes**:
   - Matches local chunks -> Grades them as **Correct**.
   - Generates answer citing the uploaded file.
5. **User submits a out-of-domain query** (e.g., "What was Microsoft's stock price yesterday?").
6. **Pipeline executes**:
   - Local chunk relevance is graded **Incorrect**.
   - Query rewritten to "Microsoft stock price June 21 2026".
   - Triggers Web Search fallback.
   - Generates answer citing web sources.

---

## 7. MVP Definition
### In Scope (v1)
- Single-user / simple auth workspace.
- Document ingestion (TXT, PDF, MD) stored in a local vector database.
- Agentic CRAG workflow using FastAPI and lightweight local libraries or LangChain.
- Fallback web search using DuckDuckGo/Tavily search client.
- Beautiful, high-end dark mode Chat UI.

---

## 8. Functional Requirements
### Backend Requirements
- Document chunking, embedding generation, and indexing.
- Relevance grading mechanism (compares query and chunk).
- Web search query rewriter and fetcher.
- WebSocket or Server-Sent Events (SSE) for streaming the response and pipeline logs.

### Frontend Requirements
- Beautiful layout with sidebar navigation.
- Real-time chat interface.
- Pipeline execution log viewer displaying each state of the CRAG flow.

---

## 9. Non-Functional Requirements
- **Performance**: Document indexing < 5 seconds per page. Web search fallback response time < 5 seconds.
- **Security**: Secure storage of API keys, CORS protections, inputs sanitized.

---

## 10. Technical Recommendations
- **Frontend**: React (Vite) + Vanilla CSS (for speed, clean aesthetics).
- **Backend**: FastAPI (Python), SQLite (for database and metadata storage), FAISS or ChromaDB (for local vector representation).
- **Web Search**: DuckDuckGo API (free, no setup required) with a fallback to Google/Tavily if configured.

---

## 11. Analytics and Evaluation
- System logs showing accuracy scores of retrieved passages.
- Query fallback statistics (e.g., % of queries requiring web search).

---

## 12. Risks and Assumptions
- *Risk*: Third-party LLM rate limits or network latency.
- *Mitigation*: Local chunk caching and fallback web search caching.

---

## 13. Out of Scope
- Multi-tenant tenant billing, complex RBAC rules, file structure sharing, database clustering.
