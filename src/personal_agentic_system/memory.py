"""Rebuildable Chroma memory using local Ollama embeddings."""

import hashlib
from pathlib import Path

import requests

from personal_agentic_system.config import Settings, settings


class MemoryStore:
    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        self._collection = None

    @property
    def collection(self):
        # Import lazily so pure workflow tests do not need a running Chroma client.
        if self._collection is None:
            import chromadb

            self.config.chroma_path.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(self.config.chroma_path))
            self._collection = client.get_or_create_collection(
                self.config.chroma_collection
            )
        return self._collection

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = requests.post(
            f"{self.config.ollama_url}/api/embed",
            json={"model": self.config.embed_model, "input": texts},
            timeout=120,
        )
        response.raise_for_status()
        embeddings = response.json().get("embeddings", [])
        if len(embeddings) != len(texts):
            raise RuntimeError("Ollama returned an unexpected embedding count")
        return embeddings

    @staticmethod
    def chunk(text: str, size: int = 1200, overlap: int = 120) -> list[str]:
        """Create readable chunks with a small boundary overlap."""
        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs:
            # Split unusually long paragraphs so embedding requests remain bounded.
            if len(paragraph) > size:
                if current:
                    chunks.append(current)
                    current = ""
                step = max(1, size - overlap)
                chunks.extend(
                    paragraph[start : start + size]
                    for start in range(0, len(paragraph), step)
                )
                continue
            candidate = f"{current}\n\n{paragraph}".strip()
            if current and len(candidate) > size:
                chunks.append(current)
                current = f"{current[-overlap:]}\n\n{paragraph}".strip()
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks

    def index_vault(self) -> dict[str, int]:
        documents: list[str] = []
        ids: list[str] = []
        metadatas: list[dict[str, str]] = []

        for note in sorted(self.config.vault_path.rglob("*.md")):
            relative = note.relative_to(self.config.vault_path).as_posix()
            text = note.read_text(encoding="utf-8")
            for position, chunk in enumerate(self.chunk(text)):
                digest = hashlib.sha256(f"{relative}:{position}".encode()).hexdigest()[:20]
                ids.append(digest)
                documents.append(chunk)
                metadatas.append({"source": relative, "chunk": str(position)})

        if documents:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=self.embed(documents),
                metadatas=metadatas,
            )
        return {"notes": len(list(self.config.vault_path.rglob('*.md'))), "chunks": len(ids)}

    def search(self, query: str, top_k: int = 5) -> list[dict[str, str | float]]:
        result = self.collection.query(
            query_embeddings=[self.embed([query])[0]],
            n_results=top_k,
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            {
                "text": document,
                "source": metadata.get("source", "unknown"),
                "distance": float(distance),
            }
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]
