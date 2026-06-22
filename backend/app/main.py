from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.core.database import init_db
from app.routers import auth, documents, chat
import os

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Factual-first QA platform with agentic document grading and fallback search.",
    version="1.0.0"
)

# CORS - allow all origins in dev; in production the frontend is served by FastAPI itself
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)

@app.on_event("startup")
def startup_event():
    init_db()
    print("Database tables initialized successfully.")

@app.get("/health")
def health_check():
    return {"status": "online", "project": settings.PROJECT_NAME}

# ── Serve built React frontend (production) ──────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")

if os.path.exists(STATIC_DIR):
    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    # Catch-all: serve index.html for any non-API route (React Router support)
    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        index = os.path.join(STATIC_DIR, "index.html")
        return FileResponse(index)
