"""
Retrieval quality evaluation.
Tests vector-only and hybrid search against known data.
Usage: python -m evals.retrieval_eval
"""
import time

from app.core.database import SessionLocal
from app.memory.models import JDArchive, UserFact


def prep_test_data(db, user_id: int = 999):
    """Insert known test JDs and facts for a test user."""
    # Clean previous
    for f in db.query(UserFact).filter(UserFact.user_id == user_id).all():
        db.delete(f)
    for j in db.query(JDArchive).filter(JDArchive.user_id == user_id).all():
        db.delete(j)
    db.commit()

    # Skills
    skills = [
        ("Python FastAPI 异步接口开发，5年经验", "skill"),
        ("Docker Kubernetes 微服务部署与运维", "skill"),
        ("RAG 检索增强生成全链路设计与优化", "skill"),
        ("LangGraph 多节点工作流编排", "skill"),
        ("MySQL PostgreSQL 数据库设计与优化", "skill"),
        ("Vue3 前端开发 SSE 流式交互", "skill"),
        ("Claude Code AI辅助编程工具使用", "skill"),
    ]
    for text, cat in skills:
        db.add(UserFact(user_id=user_id, category=cat, content=text, source="eval"))

    # JDs
    jds = [
        ("某AI公司", "Python后端工程师", "要求Python FastAPI Docker 微服务 RAG 经验", "Python,FastAPI,Docker,RAG", 75),
        ("某电商", "全栈工程师", "要求Vue React Python Django 全栈开发 Docker", "Vue,Python,Django,Docker", 60),
        ("某金融", "数据工程师", "要求Python Pandas Spark Hadoop 数据仓库 ETL", "Python,Pandas,Spark", 45),
        ("某大厂", "AI Agent开发", "要求LangGraph Agent MCP RAG LLM 大模型应用", "LangGraph,Agent,MCP,RAG", 80),
        ("某云服务", "DevOps工程师", "要求Docker K8s Terraform CI/CD Linux 运维", "Docker,K8s,Terraform,CI/CD", 55),
    ]
    for company, pos, text, tags, score in jds:
        db.add(JDArchive(user_id=user_id, company=company, position=pos,
                         jd_text=text, tags=tags, match_score=score))
    db.commit()
    return len(skills), len(jds)


def test_vector_recall(db, user_id: int):
    """Test: given a query, does vector search find the right JDs?"""
    from app.memory import vector_store as vs
    from app.memory.embeddings import embed_text

    # Index all JDs into Milvus
    archives = db.query(JDArchive).filter(JDArchive.user_id == user_id).all()
    for a in archives:
        vs.index_jd({
            "text": a.jd_text or "", "user_id": user_id, "jd_id": a.id,
            "company": a.company or "", "position": a.position or "",
            "skills": a.tags or "", "match_score": a.match_score or 0,
        })

    # Also index skills
    facts = db.query(UserFact).filter(UserFact.user_id == user_id).all()
    if facts:
        vs.index_facts([{"text": f.content, "user_id": user_id,
                          "category": f.category, "doc_id": "eval"} for f in facts])

    test_queries = [
        ("Python FastAPI Docker 后端开发", ["某AI公司", "某电商"]),
        ("AI Agent LangGraph MCP 大模型", ["某大厂"]),
        ("Vue 前端 全栈", ["某电商"]),
    ]

    print("\n=== Vector Recall Test ===")
    print(f"{'Query':<40s} {'Expected':<25s} {'Got (top3)':<50s} {'Hit'}")
    hits = 0
    total = 0
    for query, expected in test_queries:
        results = vs.search_similar_jds(query, user_id, top_k=3)
        got = [r.get("company", "") for r in results]
        hit = any(e in got for e in expected)
        total += 1
        if hit:
            hits += 1
        print(f"{query[:40]:<40s} {str(expected):<25s} {str(got):<50s} {'PASS' if hit else 'MISS'}")

    recall = hits / total if total else 0
    print(f"\nRecall@{3}: {hits}/{total} = {recall:.0%}")

    # Also test fact recall
    print("\n=== Fact Vector Recall ===")
    fact_tests = [
        ("FastAPI Python 后端", ["Python FastAPI 异步接口开发"], "skill"),
        ("Docker K8s 运维", ["Docker Kubernetes 微服务部署与运维"], "skill"),
        ("前端 Vue", ["Vue3 前端开发 SSE 流式交互"], "skill"),
    ]
    f_hits = 0
    for query, expected, cat in fact_tests:
        results = vs.search_similar_facts(query, user_id, category=cat, top_k=3)
        got_texts = [r["text"][:40] for r in results]
        hit = any(e[:30] in g for e in expected for g in got_texts)
        f_hits += 1 if hit else 0
        print(f"  {query:<30s} -> {got_texts} {'OK' if hit else 'X'}")

    print(f"Fact Recall: {f_hits}/{len(fact_tests)}")
    return recall


def cleanup(db, user_id: int):
    """Purge test data."""
    from app.memory import vector_store as vs
    for f in db.query(UserFact).filter(UserFact.user_id == user_id).all():
        db.delete(f)
    for j in db.query(JDArchive).filter(JDArchive.user_id == user_id).all():
        db.delete(j)
    db.commit()
    vs.delete_user_facts(user_id)


if __name__ == "__main__":
    db = SessionLocal()
    try:
        n_skills, n_jds = prep_test_data(db, user_id=999)
        print(f"Prepared: {n_skills} skills, {n_jds} JDs for test user 999")
        recall = test_vector_recall(db, user_id=999)
        cleanup(db, user_id=999)
        print("\nDone. Recall = recall rate of finding relevant results in top K.")
    finally:
        db.close()
