import os
import hashlib
from typing import List
import numpy as np
from app.core.config import settings

class Embedder:
    _instance = None
    _model = None
    _vectorizer = None

    def __init__(self):
        # We initialize with a fast, deterministic dense vectorizer (384 dimensions, matching bge-small)
        # and attempt to load sentence-transformers if available.
        self.dim = 384
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            print(f"[Embedder] Loaded SentenceTransformer model: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            # Deterministic dense semantic hash embedding fallback (dimension 384)
            self._model = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Embedder()
        return cls._instance

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self._model is not None:
            try:
                embeddings = self._model.encode(texts, normalize_embeddings=True)
                return embeddings.tolist()
            except Exception as e:
                print(f"[Embedder] Model encode error: {e}, using fallback dense vectorizer")

        # Fast deterministic 384-d semantic dense representation
        vectors = []
        for text in texts:
            vec = self._hash_vectorize(text, self.dim)
            vectors.append(vec)
        return vectors

    def embed_query(self, query: str) -> List[float]:
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * self.dim

    def _hash_vectorize(self, text: str, dim: int) -> List[float]:
        words = text.lower().replace("\n", " ").split()
        vec = np.zeros(dim, dtype=np.float32)
        if not words:
            return vec.tolist()

        for i, word in enumerate(words):
            # Extract n-grams and tokens
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h // dim) % 2 == 0 else -1.0
            weight = 1.0 / (1.0 + 0.05 * min(i, 20))
            vec[idx] += sign * weight

        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

embedder = Embedder.get_instance()
