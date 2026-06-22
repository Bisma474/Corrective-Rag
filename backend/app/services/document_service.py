import os
import numpy as np
import pickle
import PyPDF2
from sentence_transformers import SentenceTransformer
from app.core.config import settings

# Load model lazily
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        # Load a small, fast model
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

class LocalVectorDB:
    def __init__(self):
        self.db_path = os.path.join(settings.STORAGE_DIR, "vector_db.pkl")
        self.load()

    def load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "rb") as f:
                data = pickle.load(f)
                self.embeddings = data.get("embeddings", [])
                self.chunks = data.get("chunks", [])
                self.doc_ids = data.get("doc_ids", [])
        else:
            self.embeddings = []
            self.chunks = []
            self.doc_ids = []

    def save(self):
        with open(self.db_path, "wb") as f:
            pickle.dump({
                "embeddings": self.embeddings,
                "chunks": self.chunks,
                "doc_ids": self.doc_ids
            }, f)

    def add_document(self, doc_id: int, text: str):
        model = get_embedding_model()
        
        # Split text into chunks of roughly 500 characters with 100 character overlap
        chunk_size = 500
        overlap = 100
        
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += chunk_size - overlap
            if start >= len(text) or end == len(text):
                break

        if not chunks:
            return

        # Compute embeddings
        chunk_embeddings = model.encode(chunks)

        for chunk, emb in zip(chunks, chunk_embeddings):
            self.chunks.append(chunk)
            self.embeddings.append(emb)
            self.doc_ids.append(doc_id)

        self.save()

    def delete_document(self, doc_id: int):
        indices_to_keep = [i for i, d_id in enumerate(self.doc_ids) if d_id != doc_id]
        
        self.embeddings = [self.embeddings[i] for i in indices_to_keep]
        self.chunks = [self.chunks[i] for i in indices_to_keep]
        self.doc_ids = [self.doc_ids[i] for i in indices_to_keep]
        
        self.save()

    def search(self, query: str, top_k: int = 3, doc_ids: list = None):
        if not self.embeddings:
            return []

        if doc_ids is not None:
            if not doc_ids:
                return []
            indices = [i for i, d_id in enumerate(self.doc_ids) if d_id in doc_ids]
            if not indices:
                return []
        else:
            indices = list(range(len(self.embeddings)))

        model = get_embedding_model()
        query_emb = model.encode([query])[0]

        # Compute cosine similarity
        filtered_embs = np.array([self.embeddings[i] for i in indices])
        norms = np.linalg.norm(filtered_embs, axis=1)
        query_norm = np.linalg.norm(query_emb)
        
        if query_norm == 0 or (norms == 0).any():
            return []

        similarities = np.dot(filtered_embs, query_emb) / (norms * query_norm)
        
        # Get top_k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            actual_idx = indices[idx]
            results.append({
                "chunk": self.chunks[actual_idx],
                "score": float(similarities[idx]),
                "doc_id": self.doc_ids[actual_idx]
            })
        return results

vector_db = LocalVectorDB()

def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt" or ext == ".md":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif ext == ".pdf":
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    return ""
