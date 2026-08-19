---
type: architecture-note
classification: synthetic
---

# Local-First Memory

Markdown notes remain the understandable source of truth. Ollama creates local
multilingual embeddings, and Chroma provides rebuildable semantic retrieval.
The vector index is derived data: it can be deleted and recreated from the notes.

For this portfolio system, `bge-m3` is the default embedding model because the
workflow should retrieve both English and Georgian material without sending the
source notes to a cloud embedding API.

