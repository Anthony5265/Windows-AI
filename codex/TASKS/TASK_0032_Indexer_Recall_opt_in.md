# Task 32: Indexer & Recall (opt‑in)

**Goal**: Local semantic search over chosen folders; fully offline.

**Scope**
- Watchers for selected paths; index text, PDFs (OCR), office docs
- Embeddings store (SQLite/FAISS); metadata (path, mtime, snippet)
- Exclusions/redaction rules; pause/resume

**Acceptance**
- Indexes ≥10k files/hour on SSD
- Search returns relevant results with snippets/paths
- Privacy: off by default; wipe index clears data
