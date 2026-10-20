import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.embeddings.embedder import embedder

class VectorStore:
    _instance = None

    def __init__(self):
        settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = VectorStore()
        return cls._instance

    def _sanitize_name(self, repo_id: str) -> str:
        clean = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in repo_id)
        name = f"repo_{clean}"
        if len(name) > 60:
            name = name[:60]
        return name

    def index_chunks(self, repo_id: str, chunks: List[Dict[str, Any]]):
        if not chunks:
            return

        collection_name = self._sanitize_name(repo_id)
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            pass

        collection = self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            ids = [f"{b['id']}_{idx}" for idx, b in enumerate(batch)]
            documents = [b["text"] for b in batch]
            metadatas = [b["metadata"] for b in batch]

            # Generate embeddings
            embeddings = embedder.embed_texts(documents)

            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )

    def query(self, repo_id: str, query_text: str, top_k: int = 6, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        collection_name = self._sanitize_name(repo_id)
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            return []

        query_embedding = embedder.embed_query(query_text)
        
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, collection.count() or 1),
                where=filter_dict if filter_dict else None
            )
        except Exception as e:
            print(f"[VectorStore] Query error: {e}")
            return []

        formatted: List[Dict[str, Any]] = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

            for doc, meta, dist in zip(docs, metas, distances):
                formatted.append({
                    "text": doc,
                    "metadata": meta,
                    "distance": dist
                })

        return formatted

    def delete_repo(self, repo_id: str):
        collection_name = self._sanitize_name(repo_id)
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            pass

vector_store = VectorStore.get_instance()
