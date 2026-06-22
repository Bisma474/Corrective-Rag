# Security and Access Document

## 1. Security Overview
The Corrective RAG (CRAG) system implements standard application-layer security principles to protect uploaded documentation and user queries.

---

## 2. Authentication Strategy
- **Token-based JWT auth**: Upon login, a token is issued containing the user identifier.
- **Session Management**: Session tokens expire after 24 hours. The tokens are stored in `localStorage` in the frontend and validated with every API request.
- **Password Hashing**: Passwords stored in SQLite are hashed using `bcrypt`.

---

## 3. Authorization
- **User Ownership**: Users can only see documents they uploaded and conversations they started.
- **Roles**:
  - `User`: Can upload files, run search queries, view logs.
  - `Admin` (future scope): Can manage system keys and delete files globally.

---

## 4. Row-Level Security
Since we are using SQLite, row-level access control is enforced in the SQL queries themselves:
```sql
SELECT * FROM documents WHERE user_id = :user_id;
SELECT * FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id = :user_id);
```

---

## 5. API Security
- **Rate Limiting**: Implementation of a simple rate limiter in the FastAPI router using `slowapi` or middleware (e.g., maximum 60 requests per minute per IP).
- **Validation**: Strict input schema validation via `Pydantic` models.
- **CORS**: Configured with explicit origins (e.g. `http://localhost:5173` for Vite/React dev server).

---

## 6. Data Protection
- **Encryption**: Uploaded documents are saved under sanitized filenames in a local storage directory (`backend/storage/`).
- **Secrets Management**: LLM keys and JWT secrets are loaded via environment variables rather than hardcoded in source.

---

## 7. Error Handling Guide
- **Login Failures**: Generic "Invalid credentials" error returned without specifying whether username or password was incorrect.
- **Upload Failures**: Clear messaging if document exceeds limit (e.g. 10MB) or is in unsupported format.
- **API Failures**: Fallback response returned to front end if LLM fails, ensuring the user gets a fallback answer instead of a raw traceback.
