<div align="center">
  <img src="./frontend/logo.png" alt="CareerPilot-AI Logo" width="420" />

  <p>
    <a href="#quick-start">Quick Start</a> ·
    <a href="#architecture">Architecture</a> ·
    <a href="#features">Features</a> ·
    <a href="#evaluation">Evaluation</a> ·
    <a href="#license">License</a>
  </p>

  <p>
    <a href="#快速开始">中文</a> | <a href="#quick-start">English</a>
  </p>
</div>

---

# CareerPilot-AI

**LLM Agent-driven career workspace: JD-resume matching, trustworthy rewriting, RAG memory, and evaluation harness.**

---

## Quick Start / 快速开始

### 1. Clone & Setup

```bash
git clone https://github.com/yangming2002/CareerPilot-AI.git
cd CareerPilot-AI
```

### 2. Backend

```bash
cd backend
cp .env.example .env          # 编辑 .env，填入你的 API Key
# 必填：OPENAI_API_KEY=你的百炼API-KEY
# 可选：JWT_SECRET_KEY、OPENAI_MODEL 等

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

API docs: http://localhost:8001/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 → register → upload resume → paste JD → analyze.

### 4. Docker

```bash
cp backend/.env.example backend/.env   # edit with your API key
docker compose up -d                   # backend + frontend, one command
```

Open http://localhost. For Milvus production deployment, change `MilvusClient("careerpilot_milvus.db")` to `MilvusClient(uri="http://milvus-host:19530")` in `backend/app/memory/vector_store.py`.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                 Frontend (Vue 3)                     │
│    Login → Workspace → JD History                    │
├──────────────────────────────────────────────────────┤
│              API Layer (FastAPI)                     │
│    /auth/*  /analysis/*  /applications/*  ...        │
├──────────────────────────────────────────────────────┤
│           Agent Layer (LangGraph)                    │
│    parse_jd → parse_resume → rule_match              │
│    → llm_analysis → integrity_guard → compose        │
│    ↓ failure: single-shot LLM → rule engine          │
├──────────────────────────────────────────────────────┤
│         RAG Memory (Milvus + SQLite)                 │
│    Write: facts → embed → HNSW index                 │
│    Read: query rewrite → vector + BM25 → RRF → TopK  │
├──────────────────────────────────────────────────────┤
│            Data Layer (SQLite)                       │
│    8 tables: users, applications, analysis_reports,  │
│    interview_reviews, written_test_reviews,          │
│    user_facts, jd_archive, status_history            │
└──────────────────────────────────────────────────────┘
```

### Repository Structure

```
CareerPilot-AI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry, CORS, exception handlers
│   │   ├── core/                # config, database, security, errors, progress
│   │   ├── models/              # SQLAlchemy models (8 tables)
│   │   ├── schemas/             # Pydantic request/response
│   │   ├── api/v1/              # REST routes (24 endpoints)
│   │   ├── services/            # analysis, LLM analysis, graph analysis,
│   │   │                          post-processor, NLP scorer
│   │   ├── agents/              # LangGraph nodes, state, graph
│   │   ├── guards/              # integrity, injection, grounding
│   │   ├── llm/                 # OpenAI-compatible client, prompts, schemas
│   │   ├── memory/              # Milvus vector store, extractor, retriever
│   │   │   └── retrieval/       # query rewriter, hybrid retriever
│   │   └── utils/               # PDF/DOCX parser
│   ├── evals/                   # evaluation harness (42+ test cases)
│   │   ├── datasets/            # test data (JD match, integrity, injection)
│   │   ├── runner.py            # eval runner
│   │   ├── ragas_eval.py        # RAG retrieval evaluation
│   │   └── generate_eval_set.py # 500-JD dataset generator
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── api/                 # Axios client + API functions
│       ├── stores/              # Pinia stores
│       ├── components/workspace/# workspace sub-panels
│       └── views/               # Workspace, Login, Register, JDHistory
├── docs/                        # PRD, TRD, scope documents
├── LICENSE                      # MIT License
└── README.md
```

---

## Features

### Agent JD-Resume Matching
LangGraph state graph orchestrates a 7-node pipeline: JD parsing → resume parsing → rule scoring → LLM deep analysis → integrity guard → report composition. Triple-layer degradation (Agent → single-shot LLM → rule engine) ensures 100% availability.

### Trustworthy Resume Rewriting
Three-line defense against LLM fabrication:
1. **IntegrityGuard**: code-rule detection of fabricated metrics, exaggerated claims
2. **Post-Processor**: jieba-segmentation verification that every suggestion has resume evidence
3. **Guard Retry Loop**: rejected suggestions fed back to LLM for rewrite (max 2 retries)

STAR methodology (Situation-Task-Action-Result) for project highlights. Missing metrics get evaluation-method-aware placeholders (e.g., "经 RAGAS 评测，使 Recall@5 由 [xxx] 提升至 [xxx]").

### RAG Memory System
- **Write**: Facts auto-extracted from every analysis → Milvus Lite (HNSW index, 1536-dim) + SQLite structured storage
- **Read**: Query rewriting (LLM) → multi-method retrieval (vector + BM25) → RRF fusion
- **Hybrid JD Search**: Full pipeline for archived JD retrieval
- **Eval**: 100% domain-level precision on 500-JD test set

### NLP Objective Scoring
TF-IDF cosine similarity + keyword coverage + skill overlap analysis provide objective calibration anchors alongside the LLM's subjective score, preventing score inflation.

### Resume Parsing & Export
- PDF/DOCX upload with automatic structured field extraction (education, skills, projects, internships)
- Missing field detection with severity-based warnings
- Markdown and PDF export (Chinese font support)

### Application Tracker
CRUD with status history and same-company cooldown detection.

---

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Current user |
| POST | `/api/v1/analysis/jd-match` | Agent JD-resume matching |
| POST | `/api/v1/analysis/rewrite-resume` | STAR resume rewrite |
| POST | `/api/v1/analysis/parse-resume` | Upload & parse PDF/DOCX |
| GET | `/api/v1/analysis/jd-history` | Hybrid JD search |
| GET | `/api/v1/analysis/export-md/{id}` | Export Markdown |
| GET | `/api/v1/analysis/export-pdf/{id}` | Export PDF |
| GET | `/api/v1/analysis/progress/{sid}` | Analysis progress |
| GET | `/api/v1/analysis/user-profile` | Memory profile |
| GET | `/api/v1/analysis/user-facts` | List extracted facts |
| CRUD | `/api/v1/applications` | Application tracker |
| POST/GET | `/api/v1/interviews/reviews` | Interview reviews |
| POST/GET | `/api/v1/written-tests/reviews` | Written-test reviews |
| GET | `/api/v1/skill-profile` | Skill profile |

---

## Evaluation

```bash
cd backend

# Full eval suite (JD match + guard + injection)
python -m evals.runner

# RAG retrieval evaluation (500 JDs)
python -m evals.ragas_eval
```

| Suite | Cases | Key Metric |
|-------|-------|------------|
| JD Match Accuracy | 7 | 100% within expected score range |
| Integrity Guard | 5 | Fabrication & exaggeration detection |
| Prompt Injection | 5 | 100% detection, 0% false positive |
| RAG Retrieval (6 JDs) | 5 | ID-level Precision@5: 100%, Recall@5: 80%, MRR: 1.00 |
| RAG Retrieval (500 JDs) | 20 | Domain-level Precision@5: 100% |

---

## Tech Stack

**Frontend**: Vue 3 · Vite · TypeScript · Pinia · Element Plus · Vue Router · Axios

**Backend**: Python 3.11+ · FastAPI · Pydantic v2 · SQLAlchemy · SQLite · LangGraph

**LLM**: Qwen-Turbo (Alibaba Bailian, OpenAI-compatible) · text-embedding-v2

**RAG**: Milvus Lite (HNSW) · rank-bm25 · RRF fusion · jieba

**Eval**: Custom harness · scikit-learn · RAGAS · NumPy

---

## Key Design Decisions

**Single Agent over Multi-Agent**: All 7 pipeline nodes have serial dependencies. Multi-agent would add coordination overhead with no parallelism benefit. Single LLM with role-switching prompts (advisor → reviewer) achieves same quality with fewer calls.

**Turbo over Plus for production**: qwen-turbo provides sufficient quality at ~5s/call. qwen-plus was 10x slower with marginal quality gains.

**Decoupled resume rewriting**: Separate from main analysis. Users trigger rewriting only when match score justifies it, saving ~40% analysis time.

**HNSW over FLAT**: Milvus index acceleration for vector search on growing JD archives.

**RRF over single-method retrieval**: Reciprocal Rank Fusion merges vector and BM25 results better than either alone.

---

## License

MIT © 2026 Yang Ming

See [LICENSE](./LICENSE) for full text.

---

<div align="center">

## 中文说明

### CareerPilot-AI — LLM Agent 驱动求职工作台

独立设计并开发的 LLM Agent 求职工作台，覆盖 JD-简历智能匹配、可信简历优化、RAG 记忆检索与自动化评测。

**核心特性**：
- **Agent 工作流**：LangGraph 7 节点流水线（解析→匹配→校验→生成），三层降级容错
- **可信改写**：三重防线防编造 + STAR 方法论 + 评测方法感知占位符
- **RAG 记忆**：Milvus HNSW + BM25 + RRF 混合检索，500 JD 评测集领域精确率 100%
- **NLP 客观评分**：TF-IDF + 关键词覆盖率校准 LLM 主观评分
- **42 用例评测体系**：覆盖匹配准确性、Guard 检出、注入防御、检索质量

**技术栈**：Python · FastAPI · LangGraph · Vue 3 · Milvus · Qwen-Turbo

</div>
