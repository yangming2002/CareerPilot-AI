<div align="center">
  <img src="./frontend/logo.png" alt="CareerPilot-AI Logo" width="420" />
  <p><strong>LLM Agent-driven career workspace: JD-resume matching, trustworthy rewriting, RAG memory, and evaluation harness.</strong></p>
  <p>
    <a href="./README_CN.md">中文文档</a>
  </p>
</div>

---

## Quick Start

```bash
git clone https://github.com/yangming2002/CareerPilot-AI.git
cd CareerPilot-AI
```

### Local Dev

```bash
# Backend
cd backend
cp .env.example .env          # Fill OPENAI_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
npm install && npm run dev
```

### Docker

```bash
cp backend/.env.example backend/.env   # 填入 API Key

# 拉预构建镜像（推荐）
docker compose pull && docker compose up -d

# 或本地构建
docker compose up --build -d
```

Open http://localhost.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                 Frontend (Vue 3)                     │
│    Login → Workspace → JD History                    │
├──────────────────────────────────────────────────────┤
│              API Layer (FastAPI)                     │
├──────────────────────────────────────────────────────┤
│           Agent Layer (LangGraph)                    │
│    parse_jd → parse_resume → rule_match              │
│    → llm_analysis → integrity_guard → compose        │
│    ↓ failure: single-shot LLM → rule engine          │
├──────────────────────────────────────────────────────┤
│         RAG Memory (Milvus + SQLite)                 │
│    Write: embed → HNSW. Read: rewrite → vector+BM25→RRF│
├──────────────────────────────────────────────────────┤
│            Data (SQLite, 8 tables)                   │
└──────────────────────────────────────────────────────┘
```

---

## Features

- **Agent JD-Resume Matching**: 7-node LangGraph pipeline, triple-layer degradation
- **Trustworthy Rewriting**: 3-line defense (Guard + Post-Processor + Retry Loop), STAR methodology
- **RAG Memory**: Milvus HNSW + BM25 + RRF. 100% domain precision on 500-JD set
- **NLP Objective Scoring**: TF-IDF + keyword coverage as LLM score calibration
- **Resume Parsing**: PDF/DOCX upload, structured extraction, Markdown/PDF export
- **Application Tracker**: CRUD + cooldown detection

---

## Evaluation

```bash
cd backend
python -m evals.runner        # JD match + guard + injection
python -m evals.ragas_eval    # RAG retrieval
```

| Suite | Cases | Key Metric |
|-------|-------|------------|
| JD Match | 7 | 100% within expected range |
| Integrity Guard | 5 | Fabrication/exaggeration detection |
| Injection Defense | 5 | 100% detection, 0% FP |
| RAG (6 JDs) | 5 | P@5: 100%, R@5: 80%, MRR: 1.00 |
| RAG (500 JDs) | 20 | Domain P@5: 100% |

---

## Tech Stack

**Frontend**: Vue 3 · Vite · TypeScript · Pinia · Element Plus

**Backend**: Python · FastAPI · Pydantic v2 · SQLAlchemy · SQLite · LangGraph

**LLM**: Qwen-Turbo (Bailian) · text-embedding-v2

**RAG**: Milvus Lite (HNSW) · rank-bm25 · RRF · jieba

---

## License

MIT © 2026 Yang Ming — see [LICENSE](./LICENSE).
