import os
import numpy as np
import pickle
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from app.core.config import settings

class LocalVectorDB:
    def __init__(self):
        self.db_path = os.path.join(settings.STORAGE_DIR, "vector_db.pkl")
        self.vectorizer = None
        self.load()

    def load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "rb") as f:
                data = pickle.load(f)
                self.chunks = data.get("chunks", [])
                self.doc_ids = data.get("doc_ids", [])
                self.vectors = data.get("vectors", [])
                vec_data = data.get("vectorizer")
                if vec_data:
                    self.vectorizer = TfidfVectorizer()
                    self.vectorizer.vocabulary_ = vec_data["vocabulary"]
                    self.vectorizer.idf_ = np.array(vec_data["idf_"])
                    self.vectorizer.stop_words_ = vec_data.get("stop_words_", "english")
                else:
                    self.vectorizer = None
        else:
            self.chunks = []
            self.doc_ids = []
            self.vectors = []
            self.vectorizer = None

    def save(self):
        vec_data = None
        if self.vectorizer and hasattr(self.vectorizer, "vocabulary_"):
            vec_data = {
                "vocabulary": self.vectorizer.vocabulary_,
                "idf_": self.vectorizer.idf_.tolist(),
                "stop_words_": self.vectorizer.stop_words_,
            }
        with open(self.db_path, "wb") as f:
            pickle.dump({
                "chunks": self.chunks,
                "doc_ids": self.doc_ids,
                "vectors": self.vectors,
                "vectorizer": vec_data,
            }, f)

    def _ensure_vectorizer(self, texts):
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
            self.vectors = self.vectorizer.fit_transform(texts).toarray()
        elif not hasattr(self.vectorizer, "vocabulary_"):
            self.vectorizer.fit(texts)
            if len(self.vectors) > 0:
                vecs = []
                for chunk in self.chunks:
                    vecs.append(self.vectorizer.transform([chunk]).toarray()[0])
                self.vectors = vecs

    def add_document(self, doc_id: int, text: str):
        chunk_size = 500
        overlap = 100

        new_chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                new_chunks.append(chunk)
            start += chunk_size - overlap
            if start >= len(text) or end == len(text):
                break

        if not new_chunks:
            return

        all_texts = self.chunks + new_chunks
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        all_vectors = self.vectorizer.fit_transform(all_texts).toarray()

        self.chunks = all_texts
        self.doc_ids = self.doc_ids + [doc_id] * len(new_chunks)
        self.vectors = all_vectors
        self.save()

    def delete_document(self, doc_id: int):
        keep = [i for i, d_id in enumerate(self.doc_ids) if d_id != doc_id]
        self.chunks = [self.chunks[i] for i in keep]
        self.doc_ids = [self.doc_ids[i] for i in keep]
        if len(self.vectors) > 0:
            self.vectors = [self.vectors[i] for i in keep]
        if len(self.chunks) > 0:
            self.vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
            self.vectors = self.vectorizer.fit_transform(self.chunks).toarray()
        else:
            self.vectors = []
            self.vectorizer = None
        self.save()

    def search(self, query: str, top_k: int = 3, doc_ids: list = None):
        if self.vectorizer is None or len(self.vectors) == 0 or len(self.chunks) == 0:
            return []

        if doc_ids is not None:
            if not doc_ids:
                return []
            indices = [i for i, d_id in enumerate(self.doc_ids) if d_id in doc_ids]
            if not indices:
                return []
        else:
            indices = list(range(len(self.vectors)))

        query_vec = self.vectorizer.transform([query]).toarray()[0]
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []

        filtered_vecs = np.array([self.vectors[i] for i in indices])
        norms = np.linalg.norm(filtered_vecs, axis=1)

        similarities = np.dot(filtered_vecs, query_vec) / (norms * query_norm + 1e-10)
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
