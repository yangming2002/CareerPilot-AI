"""
RAG evaluation using RAGAS metrics.
Evaluates the JD history hybrid retrieval pipeline.
"""
import json
import time
from dataclasses import dataclass

from app.core.database import SessionLocal
from app.memory.models import JDArchive, UserFact


@dataclass
class EvalCase:
    query: str
    expected_jd_ids: list[int]
    description: str


def prep_eval_data(db, user_id: int = 9998):
    """Insert test JDs."""
    for a in db.query(JDArchive).filter(JDArchive.user_id == user_id).all():
        db.delete(a)
    db.commit()

    jds = [
        ("某AI公司", "大模型Agent开发工程师",
         "要求：精通LangGraph、MCP协议、RAG技术，有AI Agent开发经验，熟悉FastAPI。"
         "负责多智能体系统架构设计，基于LangGraph构建主从式Agent工作流。",
         "LangGraph,Agent,MCP,RAG,FastAPI", 85),
        ("某电商", "Python后端开发工程师",
         "要求：Django/FastAPI开发经验，MySQL/Redis数据库，Docker部署，微服务架构。"
         "负责电商平台后端服务开发与维护。",
         "Python,FastAPI,Django,MySQL,Docker", 70),
        ("某硬件公司", "嵌入式开发工程师",
         "要求：MCU/ARM开发，C/C++编程，电路调试，传感器应用，Arduino/STM32经验。"
         "负责智能硬件原型搭建与调试。",
         "MCU,C++,ARM,传感器,Arduino", 40),
        ("某云服务", "DevOps/SRE工程师",
         "要求：Docker/K8s运维，CI/CD流水线，Terraform基础设施即代码，Linux系统管理。"
         "负责云原生基础设施维护。",
         "Docker,K8s,CI/CD,Terraform,Linux", 55),
        ("某金融科技", "数据分析师",
         "要求：Python/Pandas数据处理，SQL数据查询，机器学习基础，Tableau/PowerBI可视化。"
         "负责金融数据分析与报表开发。",
         "Python,Pandas,SQL,机器学习,Tableau", 60),
        ("某推荐系统", "算法工程师",
         "要求：深度学习/TensorFlow/PyTorch，推荐系统算法，大规模数据处理，Spark/Hadoop。"
         "负责推荐算法研发与优化。",
         "深度学习,PyTorch,推荐系统,Spark,TensorFlow", 45),
    ]
    saved = []
    for company, pos, text, tags, score in jds:
        a = JDArchive(user_id=user_id, company=company, position=pos,
                      jd_text=text, tags=tags, match_score=score)
        db.add(a)
        db.flush()
        saved.append(a.id)
    db.commit()
    return saved


def run_eval(db, user_id: int):
    """Run RAGAS-compatible evaluation metrics."""
    from app.memory.retrieval.hybrid_retriever import HybridRetriever

    test_cases = [
        EvalCase("AI Agent 大模型开发", [0, 1], "应召回 Agent + 部分后端（都涉及Python）"),
        EvalCase("嵌入式硬件 MCU Arduino", [2], "应只召回硬件 JD"),
        EvalCase("Python FastAPI 后端", [1, 0, 4], "应召回后端 + AI + 数据（都有Python）"),
        EvalCase("Docker K8s 运维", [3, 1], "应召回 DevOps + 后端"),
        EvalCase("机器学习 推荐系统", [5, 4], "应召回算法 + 数据"),
    ]

    # Get saved JD IDs
    jds = db.query(JDArchive).filter(JDArchive.user_id == user_id).all()
    id_map = {i: jds[i].id for i in range(len(jds))}  # index -> db_id

    retriever = HybridRetriever(db, user_id)

    results = []
    for case in test_cases:
        start = time.time()
        retrieved = retriever.search(case.query, top_k=5)
        elapsed = time.time() - start

        retrieved_ids = [r.jd_id for r in retrieved]
        expected_ids = [id_map[i] for i in case.expected_jd_ids if i in id_map]

        # Metrics
        hits = len(set(retrieved_ids) & set(expected_ids))
        precision = hits / len(retrieved_ids) if retrieved_ids else 0
        recall = hits / len(expected_ids) if expected_ids else 1

        # MRR: Mean Reciprocal Rank
        mrr = 0.0
        for i, rid in enumerate(retrieved_ids):
            if rid in expected_ids:
                mrr = 1.0 / (i + 1)
                break

        # NDCG@5: higher rank + more relevant = higher score
        dcg = sum(1.0 / np.log2(i + 2) for i, rid in enumerate(retrieved_ids) if rid in expected_ids) if retrieved_ids else 0
        idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(expected_ids), len(retrieved_ids))))
        ndcg = dcg / idcg if idcg > 0 else 0

        results.append({
            "query": case.query,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "mrr": round(mrr, 3),
            "ndcg": round(ndcg, 3),
            "time": round(elapsed, 2),
            "expected": [id_map[i] for i in case.expected_jd_ids if i in id_map],
            "got": retrieved_ids[:5],
        })
        print(f"  {case.query[:30]:<30s} P={precision:.2f} R={recall:.2f} MRR={mrr:.2f} NDCG={ndcg:.2f} ({elapsed:.1f}s)")

    return results


def cleanup(db, user_id: int):
    for a in db.query(JDArchive).filter(JDArchive.user_id == user_id).all():
        db.delete(a)
    db.commit()


if __name__ == "__main__":
    import numpy as np

    db = SessionLocal()
    try:
        ids = prep_eval_data(db, user_id=9998)
        print(f"Prepared {len(ids)} JDs for eval\n")

        results = run_eval(db, user_id=9998)

        # Summary
        avg_p = np.mean([r["precision"] for r in results])
        avg_r = np.mean([r["recall"] for r in results])
        avg_m = np.mean([r["mrr"] for r in results])
        avg_n = np.mean([r["ndcg"] for r in results])
        avg_t = np.mean([r["time"] for r in results])

        print(f"\n{'='*50}")
        print(f"RAG Evaluation Summary")
        print(f"{'='*50}")
        print(f"Precision@5: {avg_p:.3f}  (top5中有多少是相关的)")
        print(f"Recall@5:    {avg_r:.3f}  (相关JD有多少被召回)")
        print(f"MRR:         {avg_m:.3f}  (第一个相关结果的平均排名倒数)")
        print(f"NDCG@5:      {avg_n:.3f}  (排序质量)")
        print(f"Avg time:    {avg_t:.1f}s")

        cleanup(db, user_id=9998)
        print("\nDone.")
    finally:
        db.close()
