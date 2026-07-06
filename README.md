<div align="center">
  <img src="./frontend/logo.png" alt="CareerPilot-AI Logo" width="420" />
  <p><strong>Agent-driven career workspace: JD-resume matching, trustworthy rewriting, RAG memory, and evaluation harness.</strong></p>
  <p>
    <a href="./README_CN.md">中文文档</a>
  </p>
</div>

---

## Quick Start

```bash
git clone https://github.com/yangming2002/CareerPilot-AI.git
cd CareerPilot-AI

# Local
cd backend && cp .env.example .env && pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
cd frontend && npm install && npm run dev

# Docker
cp backend/.env.example backend/.env && docker compose up --build -d
```

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                 Frontend (Vue 3)                      │
│    Login → Workspace → JD History → KB → Memory      │
├──────────────────────────────────────────────────────┤
│              API Layer (FastAPI, 24 endpoints)        │
├──────────────────────────────────────────────────────┤
│           Agent Layer (LangGraph, 7-node pipeline)    │
│    parse_both → rule_match → llm_analysis             │
│    → integrity_guard → compose                        │
│    ↓ failure: single-shot LLM → rule engine           │
├──────────────────────────────────────────────────────┤
│         RAG Memory (Milvus HNSW + SQLite)             │
│    Hybrid: query rewrite → vector + BM25 → RRF        │
├──────────────────────────────────────────────────────┤
│            Data (SQLite, 10 tables)                   │
└──────────────────────────────────────────────────────┘
```

---

## Design Decisions

### Why qwen-turbo, not qwen-plus?

| Model | Latency | Quality | Verdict |
|-------|---------|---------|---------|
| qwen-turbo | ~10s/call | Sufficient for matching | **Production** |
| qwen-plus | ~40s/call | Marginal improvement | Rejected: 4x slower, negligible gain |

Measured on real JD-resume pairs (n=5). qwen-turbo achieves 100% score accuracy on eval set.

### Why Hybrid Retrieval (Vector + BM25)?

| Method | Recall@5 | Domain Precision | Notes |
|--------|----------|------------------|-------|
| Vector only | 80% | 85% | Misses exact keyword matches like "MCU", "STM32" |
| BM25 only | 60% | 72% | Misses semantic equivalents like "容器化" ↔ "Docker" |
| **Hybrid (RRF)** | **100%** | **100%** | Combines both strengths |

Vector embedding (text-embedding-v2, 1536-dim) captures semantic similarity. BM25 captures exact technical term matching. RRF fusion merges rankings without score calibration. On a 500-JD test set spanning 10 domains, hybrid achieved 100% domain-level precision with zero cross-domain errors.

### Why LangGraph, not LangChain?

LangGraph provides a **state graph with conditional routing**. The integrity guard creates a cycle:

```
llm_analysis → guard → fail? → back to llm_analysis (retry with feedback)
                    → pass? → compose
```

LangChain Chains are linear A→B→C and cannot express this loop. LangGraph's `StateGraph` + `add_conditional_edges` handles the guard retry pattern natively.

### PDF Parsing

Two-layer strategy for reliability:

| Layer | Library | Role |
|-------|---------|------|
| Primary | pymupdf (fitz) | Extracts text with Unicode/CJK support. Handles most modern PDFs |
| Fallback | pdfplumber | Called only when pymupdf returns empty text |

The `extract_text()` function in `utils/file_parser.py` chains both parsers. Font descriptor warnings from pdfminer are suppressed. Scanned/image-based PDFs without a text layer trigger a clear error message directing users to paste text manually.

---

## Challenges & Solutions

| Challenge | Why It Was Hard | Solution |
|-----------|----------------|---------|
| **LLM fabricates metrics** | LLM tends to add fake numbers ("improved 50%") when resume lacks quantification | Three-layer defense: IntegrityGuard (code) → PostProcessor (jieba) → Retry loop (LLM feedback). Injection defense: 100% detection rate on 500 cases |
| **Score clustering at 75** | LLM hesitant to give very low scores, all results clustered 70-80 | Added explicit scoring anchors with examples ("JD requires signal processing, resume is AI → must ≤15"). Post-processor removes hallucinated gaps via jieba segmentation |
| **"At least one" logic** | JD says "Python/Go/C++ at least one" but LLM marks all three as missing | Code-level post-processing rule: if resume covers one in group, mark all as covered |
| **Chinese PDF font issues** | Some PDFs trigger `Could not get FontBBox` warnings from pdfminer | Switched primary parser to pymupdf. Suppressed pdfminer warnings. Both parsers chained for resilience |
| **Response latency** | Initial pipeline: 3 serial LLM calls + archival LLM call = 40-60s | Parallelized JD/resume parsing (ThreadPoolExecutor). Made archival fact extraction async (background thread). Prompt compacted. Total reduced from ~44s to ~17s |
| **Frontend progress was fake** | Timer-based progress bar ("30s elapsed") didn't reflect backend reality | Replaced with structured `_tool_step()` logging. Each node reports [done] status with details. Loader shows actual backend steps post-response |
| **Bailian json_object requirement** | Bailian rejects `response_format: json_object` unless user message contains "json" | Added `(Please respond with a JSON object.)` suffix. For complex schemas, fall back to plain `complete()` + manual JSON parse |

---

## Evaluation

```bash
cd backend
python -m evals.runner              # Full suite
python -m evals.runner --suite integrity  # Guard only
python -m evals.ragas_eval          # Retrieval eval
```

| Suite | Cases | Metric | Score |
|-------|-------|--------|-------|
| JD Match Accuracy | 7 | Score within expected range | 100% |
| Guard Detection (code) | 4 | Fabrication/exaggeration caught | 50% (code), needs LLM Guard |
| Prompt Injection | 500 | Detection rate, false positive | 100% detection, 0% FP |
| RAG Retrieval (6 JDs, ID-level) | 5 queries | Precision@5, Recall@5, MRR | P:100%, R:80%, MRR:1.00 |
| RAG Retrieval (500 JDs, domain-level) | 20 queries | Domain Precision@5 | 100%, zero cross-domain errors |
| Hybrid vs Vector-only | 20 queries | Recall uplift | +20% (80% → 100%) |
| Agent Pipeline Latency | 5 pairs | End-to-end | ~17s avg |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3 · Vite · TypeScript · Pinia · Element Plus |
| Backend | Python · FastAPI · Pydantic v2 · SQLAlchemy · SQLite |
| Agent | LangGraph (StateGraph + conditional edges) |
| LLM | Qwen-Turbo (Alibaba Bailian, OpenAI-compatible) |
| Embeddings | text-embedding-v2 (1536-dim, Bailian API) |
| Vector DB | Milvus Lite (HNSW, COSINE) — local file, production swap to Milvus Standalone |
| Retrieval | Hybrid: vector (Milvus) + BM25 (rank-bm25) + RRF fusion + jieba |
| Eval | Custom harness · scikit-learn · NumPy · RAGAS |

---

## License

MIT © 2026 Yang Ming — see [LICENSE](./LICENSE).
