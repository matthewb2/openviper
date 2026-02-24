from typing import Any
import numpy as np
from datetime import datetime


class VectorStore:
    def __init__(self, embedding_dim: int = 1536):
        self.embedding_dim = embedding_dim
        self.vectors: list[np.ndarray] = []
        self.metadata: list[dict[str, Any]] = []
        self.documents: list[str] = []

    def add(self, text: str, metadata: dict[str, Any] | None = None):
        embedding = self._create_embedding(text)
        self.vectors.append(embedding)
        self.documents.append(text)
        self.metadata.append(metadata if metadata is not None else {})

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_embedding = self._create_embedding(query)
        
        similarities = []
        for i, vec in enumerate(self.vectors):
            sim = self._cosine_similarity(query_embedding, vec)
            similarities.append((i, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for i, score in similarities[:top_k]:
            results.append({
                "text": self.documents[i],
                "metadata": self.metadata[i],
                "score": float(score)
            })
        
        return results

    def _create_embedding(self, text: str) -> np.ndarray:
        try:
            import hashlib
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            np.random.seed(hash_val % (2**32))
        except:
            np.random.seed(0)
        
        return np.random.randn(self.embedding_dim)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)

    def get_all(self) -> list[dict[str, Any]]:
        return [
            {"text": doc, "metadata": meta}
            for doc, meta in zip(self.documents, self.metadata)
        ]

    def clear(self):
        self.vectors.clear()
        self.metadata.clear()
        self.documents.clear()

    def count(self) -> int:
        return len(self.documents)

    def save(self, filepath: str):
        import pickle
        data = {
            "vectors": self.vectors,
            "metadata": self.metadata,
            "documents": self.documents,
            "embedding_dim": self.embedding_dim
        }
        with open(filepath, "wb") as f:
            pickle.dump(data, f)

    def load(self, filepath: str):
        import pickle
        with open(filepath, "rb") as f:
            data = pickle.load(f)
        self.vectors = data["vectors"]
        self.metadata = data["metadata"]
        self.documents = data["documents"]
        self.embedding_dim = data["embedding_dim"]
