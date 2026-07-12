import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Corrective RAG (CRAG) Platform"
    JWT_SECRET: str = "super-secret-key-crag-platform"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    PERSIST_DIR: str = os.environ.get("PERSIST_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
    STORAGE_DIR: str = os.path.join(PERSIST_DIR, "storage")
    DATABASE_DIR: str = os.path.join(PERSIST_DIR, "db")
    DATABASE_URL: str = f"sqlite:///{DATABASE_DIR}/database.db"
    
    GROQ_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure storage and database directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.DATABASE_DIR, exist_ok=True)
