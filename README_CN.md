<div align="center">
  <img src="./frontend/logo.png" alt="CareerPilot-AI Logo" width="420" />
  <p><strong>LLM Agent 驱动求职工作台：JD-简历匹配、可信改写、RAG 记忆、自动化评测</strong></p>
  <p>
    <a href="./README.md">English</a>
  </p>
</div>

---

## 快速开始

```bash
git clone https://github.com/yangming2002/CareerPilot-AI.git
cd CareerPilot-AI
```

### 本地开发

```bash
# 后端
cd backend
cp .env.example .env          # 填入 OPENAI_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 前端
cd frontend
npm install && npm run dev
```

### Docker 部署

```bash
cp backend/.env.example backend/.env   # 填入 API Key

# 拉预构建镜像（推荐）
docker compose pull && docker compose up -d

# 或本地构建
docker compose up --build -d
```

访问 http://localhost。

---

## 架构

```
┌──────────────────────────────────────────────────────┐
│                 前端 (Vue 3)                          │
│    登录 → 工作台 → JD 历史                            │
├──────────────────────────────────────────────────────┤
│              API 层 (FastAPI)                         │
├──────────────────────────────────────────────────────┤
│            Agent 层 (LangGraph)                       │
│    解析JD → 解析简历 → 规则评分                        │
│    → LLM 分析 → Guard 校验 → 汇总                     │
│    ↓ 失败 → 单次LLM → 规则引擎                         │
├──────────────────────────────────────────────────────┤
│          RAG 记忆 (Milvus + SQLite)                   │
│    写入: embed → HNSW   检索: 改写→向量+BM25→RRF      │
├──────────────────────────────────────────────────────┤
│             数据层 (SQLite, 8张表)                    │
└──────────────────────────────────────────────────────┘
```

---

## 核心功能

### Agent JD-简历匹配
LangGraph 7 节点流水线 + 三层降级容错（Agent → 单次 LLM → 规则引擎），100% 可用。

### 可信简历改写
三道防线防止 LLM 编造经历：
1. **IntegrityGuard**：代码规则检测编造指标、夸大表述
2. **后处理器**：jieba 分词校验每条建议是否有简历原文依据
3. **Guard 重试闭环**：不合格的建议反馈给 LLM 重写（最多 2 次）

STAR 方法论重构项目亮点。缺失指标自动生成评测方法感知的占位符（如"经 RAGAS 评测，使 Recall@5 由 [xxx] 提升至 [xxx]"）。

### RAG 记忆系统
- **写入**：每次分析自动抽取事实 → Milvus Lite (HNSW, 1536维) + SQLite
- **检索**：查询改写 (LLM) → 多路召回（向量 + BM25）→ RRF 融合
- **评测**：500 条 JD 评测集，领域级精确率 100%

### NLP 客观评分
TF-IDF 余弦相似度 + 关键词覆盖率 + 技能重叠分析，作为 LLM 主观评分的客观校准锚。

### 简历解析与导出
PDF/DOCX 上传自动结构化提取（教育、技能、项目、实习），缺失字段分级提醒，Markdown/PDF 导出。

### 投递追踪
CRUD + 状态历史 + 冷静期检测。

---

## 评测

```bash
cd backend
python -m evals.runner        # JD匹配 + Guard + 注入
python -m evals.ragas_eval    # RAG检索
```

| 评测套件 | 用例数 | 关键指标 |
|---------|--------|---------|
| JD 匹配准确性 | 7 | 100% 命中预期区间 |
| 完整性检查 | 5 | 编造/夸大检测 |
| 注入防御 | 5 | 100% 检测，0% 误报 |
| RAG 检索 (6 JDs) | 5 | P@5: 100%, R@5: 80%, MRR: 1.00 |
| RAG 检索 (500 JDs) | 20 | 领域 P@5: 100% |

---

## 技术栈

**前端**：Vue 3 · Vite · TypeScript · Pinia · Element Plus

**后端**：Python · FastAPI · Pydantic v2 · SQLAlchemy · SQLite · LangGraph

**LLM**：Qwen-Turbo (阿里云百炼) · text-embedding-v2

**RAG**：Milvus Lite (HNSW) · rank-bm25 · RRF · jieba

---

## 设计决策

**单 Agent 而非多 Agent**：7 个节点全部串行依赖，多 Agent 只会增加协调开销无并行收益。单个 LLM 通过 prompt 切换角色（顾问→审稿→教练）达到相同质量，调用次数更少。

**Turbo 而非 Plus**：qwen-turbo 在 ~5s/次调用下提供足够质量，qwen-plus 慢 10 倍但质量提升有限。

**简历改写解耦**：从主分析流程中独立出来，用户只在匹配分合理时才触发改写，节省约 40% 分析时间。

**HNSW 而非 FLAT**：Milvus 索引加速向量搜索。

**RRF 融合**：倒数排名融合（Reciprocal Rank Fusion）合并向量和 BM25 结果，优于单一检索方法。

---

## 开源协议

MIT © 2026 Yang Ming — 详见 [LICENSE](./LICENSE)。
