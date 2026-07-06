# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CareerPilot-AI is an LLM Agent-driven career workspace: JD-resume matching, trustworthy rewriting, RAG memory, and evaluation harness. Users upload resumes, paste JDs, and the system analyzes matches, generates optimization suggestions, and maintains a personal career memory.

## Commands

```bash
# Backend
cd backend
cp .env.example .env          # Fill OPENAI_API_KEY (Alibaba Bailian)
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
npm install && npm run dev

# Docker
docker compose up --build -d

# Eval
cd backend
python -m evals.runner                    # Full eval suite
python -m evals.runner --suite integrity  # Guard only
python -m evals.ragas_eval                # RAG retrieval eval
```

## Architecture

**Backend stack**: FastAPI + LangGraph + OpenAI SDK (Bailian qwen-turbo) + Milvus Lite + SQLite
**Frontend stack**: Vue 3 + Vite + Pinia + Element Plus + TypeScript

### Key Layers

- `backend/app/agents/` — LangGraph state graph (7-node pipeline). Entry: `parse_both` → `rule_match` → `llm_analysis` → `integrity_guard` → `compose`. Conditional edge on guard failure → retry LLM (max 2).
- `backend/app/guards/` — IntegrityGuard detects fabrication/exaggeration. GroundingGuard checks suggestion evidence. GuardRunner orchestrates.
- `backend/app/memory/` — Milvus vector store (HNSW, 1536-dim) for JD archive + user facts. HybridRetriever: query rewrite → vector + BM25 → RRF fusion.
- `backend/app/llm/` — OpenAI-compatible client (`LLMClient`), prompt templates (`prompts.py`), structured schemas (`schemas.py`). **Critical**: Bailian requires `(Please respond with a JSON object.)` in user message for `json_object` format.
- `backend/app/services/` — `GraphAnalysisService` (primary), `LLMAnalysisService` (fallback), `AnalysisService` (rule engine fallback), `MatchPostprocessor` (5 code rules), `NLPScorer` (TF-IDF + keywords).
- `backend/app/knowledge/` — Document upload → chunk → embed → Milvus index. Multiple KB types.
- `backend/app/agent_chat/` — **NOT in use**. Was a conversational Agent experiment, reverted via git reset. Code exists but not wired.

### Data Flow

1. User uploads resume (PDF/DOCX) → `parse-resume` endpoint → pymupdf extracts text → LLM structures into fields
2. User clicks "开始分析" → `POST /analysis/jd-match` → LangGraph pipeline → JDMatchResponse
3. Post-analysis: `MatchPostprocessor` corrects LLM mistakes, `_archive_analysis` stores JD + extracts facts
4. User clicks "生成改写简历" → `POST /analysis/rewrite-resume` → separate LLM call (not part of main pipeline)

### Degradation Chain

Agent (LangGraph) → Single-shot LLM → Rule engine. Each failure logged, `degraded_reason` shown in frontend.

### Key Design Decisions

- **Turbo over Plus**: qwen-turbo ~10s/call, qwen-plus ~40s. Quality difference marginal.
- **Resume rewriting decoupled**: Separate from main analysis. Saves ~40% analysis time.
- **Single Agent, not Multi-Agent**: All pipeline nodes have serial dependencies. Multi-agent adds overhead without parallelism benefit.
- **JD → Vector, Resume Facts → SQL**: JDs are many/diverse (vector search). User facts are few/stable (SQL query).
- **HNSW over FLAT**: Milvus index acceleration.

## Important Caveats

- Bailian API is slow from some networks. qwen-turbo is the fastest option available.
- `response_format={"type": "json_object"}` requires "json" in user message for Bailian.
- Milvus Lite uses local file. Delete `careerpilot_milvus.db` when dimension (1536) changes.
- SQLite DB must be deleted when schema changes (no migrations).
- Chinese text in terminal may appear garbled — this is encoding, not data corruption.
- `parse_both` node has `pool.submit()` without `.result()` — the Future fix was reverted. The node technically submits parsing to background threads but doesn't wait for them. This means parsed JD/resume data may not be available for downstream nodes.
- The `chat` agent experiment (`backend/app/agent_chat/`, `frontend/src/views/ChatView.vue`) was reverted via `git reset --hard 3ed54eb`. Stashed changes available via `git stash pop`.
