# ─────────────────────────────────────────────────────────────
# Stage 1: Build React frontend
# ─────────────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /workspace

COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install

COPY frontend/ ./frontend/

# Build outputs to frontend/dist (per vite.config.js outDir setting)
RUN cd frontend && npm run build


# ─────────────────────────────────────────────────────────────
# Stage 2: Python production image
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS production

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

# Copy built frontend from Stage 1
COPY --from=frontend-builder /workspace/frontend/dist ./static

# Create persistent directories for DB, uploads, and vector store
RUN mkdir -p /data/storage /data/db

# Expose port (HF Spaces expects port 7860)
EXPOSE 7860

# Start FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
