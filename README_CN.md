<div align="center">
  <img src="./frontend/logo.png" alt="CareerPilot-AI Logo" width="420" />
  <p><strong>Agent 驱动求职工作台：JD-简历匹配、可信改写、RAG 记忆、自动化评测</strong></p>
  <p><a href="./README.md">English</a></p>
</div>

---

## 快速开始

```bash
git clone https://github.com/yangming2002/CareerPilot-AI.git
cd CareerPilot-AI

# 本地
cd backend && cp .env.example .env && pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
cd frontend && npm install && npm run dev

# Docker
cp backend/.env.example backend/.env && docker compose up --build -d
```

---

## 设计决策

### 为什么用 qwen-turbo 而不是 qwen-plus？

| 模型 | 延迟 | 质量 | 结论 |
|------|------|------|------|
| qwen-turbo | ~10s/次 | 匹配分析够用 | **生产使用** |
| qwen-plus | ~40s/次 | 提升有限 | 拒绝：慢 4 倍，质量无明显差距 |

实测 5 组真实 JD-简历对，turbo 在评测集上匹配准确率 100%。

### 为什么混合检索（向量 + BM25）？

| 方法 | Recall@5 | 领域精确率 | 说明 |
|------|----------|-----------|------|
| 纯向量 | 80% | 85% | 丢失精确关键词如"MCU""STM32" |
| 纯 BM25 | 60% | 72% | 丢失语义等价如"容器化" ↔ "Docker" |
| **混合 (RRF)** | **100%** | **100%** | 互补优势 |

向量嵌入（text-embedding-v2, 1536 维）捕捉语义相似度，BM25 捕获精确技术术语匹配，RRF 融合两者排名无需分数校准。500 条 JD 跨 10 领域评测集上混合检索领域精确率 100%，零跨领域误召回。

### 为什么 LangGraph 而不是 LangChain？

LangGraph 提供带条件路由的**状态图**。完整性校验制造了一个环路：

```
LLM 分析 → Guard 校验 → 失败？→ 回到 LLM 分析（带反馈重试）
                     → 通过？→ 汇总输出
```

LangChain 的 Chain 是线性的 A→B→C，无法表达这个循环。LangGraph 的 `StateGraph` + `add_conditional_edges` 原生支持。

### PDF 解析方案

两层策略保障可靠性：

| 层 | 库 | 角色 |
|----|-----|------|
| 主解析 | pymupdf (fitz) | Unicode/CJK 支持，处理大多数现代 PDF |
| 降级 | pdfplumber | pyumupdf 返回空时才调用 |

`utils/file_parser.py` 中的 `extract_text()` 串联两个解析器，屏蔽 pdfminer 字体警告。扫描件/图片 PDF 无文字层时给出明确中文提示。

---

## 难点与解决

| 难点 | 根因 | 方案 |
|------|------|------|
| **LLM 编造指标** | 简历缺乏量化数据时 LLM 倾向添加假数字 | 三重防线：IntegrityGuard（代码）→ PostProcessor（jieba）→ 重试闭环（LLM 反馈）。注入防御 500 例 100% 拦截 |
| **打分扎堆 75 分** | LLM 不敢打很低的分数 | 添加显式锚点（"JD 要求信号处理，简历是 AI → 必须 ≤15"）。后处理器通过 jieba 分词移除幻觉缺口 |
| **"至少一门"逻辑** | JD 说"Python/Go/C++ 至少一门"，LLM 把三门都标缺失 | 代码后处理规则：简历覆盖同组中一项即标记全部覆盖 |
| **中文 PDF 字体** | 部分 PDF 触发 pdfminer 字体描述符警告 | 切换到 pymupdf 做主解析器，屏蔽 pdfminer 警告 |
| **响应延迟** | 初始管线含 3 次串行 LLM 调用 + 归档调用 = 40-60s | JD/简历并行解析（ThreadPoolExecutor），归档提取改为后台线程异步，prompt 精简，总耗时降至 ~17s |
| **前端进度是假进度条** | 基于计时器估算，和后端实际步骤无关 | 替换为结构化 `_tool_step()` 日志，每步标注 [done] 状态和详情 |
| **百炼 json_object 限制** | 百炼要求 user message 含 "json" 才接受 json_object 格式 | 追加 `(Please respond with a JSON object.)`。复杂 schema 退回到纯 `complete()` + 手动 JSON 解析 |

---

## 评测指标

| 套件 | 用例数 | 指标 | 分数 |
|------|--------|------|------|
| JD 匹配准确性 | 7 | 命中预期区间 | 100% |
| Guard 检出（代码级） | 4 | 编造/夸大检测 | 50%，需 LLM Guard 补充 |
| 注入防御 | 500 | 检测率，误报率 | 100% 检测，0% 误报 |
| RAG 检索（6 JD） | 5 查询 | Precision@5, Recall@5, MRR | P:100%, R:80%, MRR:1.00 |
| RAG 检索（500 JD） | 20 查询 | 领域精确率 | 100%，零跨领域误召回 |
| 混合 vs 纯向量 | 20 查询 | Recall 提升 | +20%（80% → 100%） |
| Agent 延迟 | 5 组 | 端到端 | ~17s 平均 |

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 · Vite · TypeScript · Pinia · Element Plus |
| 后端 | Python · FastAPI · Pydantic v2 · SQLAlchemy · SQLite |
| Agent | LangGraph（StateGraph + 条件边） |
| LLM | Qwen-Turbo（阿里云百炼，OpenAI 兼容协议） |
| 嵌入 | text-embedding-v2（1536 维，百炼 API） |
| 向量库 | Milvus Lite（HNSW, COSINE），生产切换到 Milvus Standalone |
| 检索 | 混合：向量（Milvus）+ BM25（rank-bm25）+ RRF 融合 + jieba |
| 评测 | 自研 Harness · scikit-learn · NumPy · RAGAS |

---

## 协议

MIT © 2026 Yang Ming — 详见 [LICENSE](./LICENSE)。
