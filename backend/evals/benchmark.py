"""
Comprehensive benchmark: latency, accuracy, throughput.
Usage: python -m evals.benchmark
"""
import json
import time
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field

EVALS_DIR = Path(__file__).resolve().parent
DATASETS = EVALS_DIR / "datasets"


@dataclass
class BenchResult:
    name: str
    latency_avg: float = 0
    latency_p50: float = 0
    latency_p95: float = 0
    accuracy: float = 0
    errors: int = 0
    total: int = 0
    details: list[dict] = field(default_factory=list)


# ── Benchmark 1: Agent Pipeline Latency ──

def bench_latency():
    """Measure end-to-end Agent pipeline latency."""
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.services.graph_analysis_service import GraphAnalysisService
    from app.core.security import hash_password

    db = SessionLocal()
    user = db.query(User).filter(User.email == "bench@test.com").first()
    if not user:
        user = User(email="bench@test.com", username="bench", hashed_password=hash_password("bench"))
        db.add(user); db.commit(); db.refresh(user)

    cases = [
        ("高匹配·全栈", "Python全栈6年，精通Django FastAPI Vue Docker K8s。参与日活200万电商平台开发，负责后端架构设计和前端性能优化。计算机硕士学历。",
         "高级全栈工程师 要求Python Django FastAPI Docker K8s 5年经验 硕士优先"),
        ("中级·跨方向", "数据分析师3年，Python Pandas SQL 机器学习基础 scikit-learn。有数据可视化Tableau经验。",
         "Python后端开发 3年经验 Django FastAPI RESTful API MySQL Redis Docker"),
        ("弱匹配·不同领域", "嵌入式开发3年，C++ ARM MCU STM32 Arduino 传感器调试 电路设计。",
         "高级Python工程师 FastAPI RAG LangGraph AI Agent开发"),
    ]

    service = GraphAnalysisService()
    times = []
    scores = []
    errors = 0

    for label, resume, jd in cases * 3:  # run each 3x for stability
        t0 = time.time()
        try:
            result = service.analyze(db, resume, jd, user.id, session_id="")
            elapsed = time.time() - t0
            times.append(elapsed)
            scores.append(result.match_score)
        except Exception:
            errors += 1

    db.close()
    return BenchResult(
        name="Agent Pipeline Latency",
        latency_avg=round(np.mean(times), 1),
        latency_p50=round(np.percentile(times, 50), 1),
        latency_p95=round(np.percentile(times, 95), 1),
        total=len(times) + errors,
        errors=errors,
        details=[{"latency": round(t, 1) for t in times}],
    )


# ── Benchmark 2: Match Score Accuracy ──

def bench_accuracy():
    """Run against labeled test cases and compute accuracy."""
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.services.graph_analysis_service import GraphAnalysisService
    from app.core.security import hash_password

    db = SessionLocal()
    user = db.query(User).filter(User.email == "bench2@test.com").first()
    if not user:
        user = User(email="bench2@test.com", username="bench2", hashed_password=hash_password("bench2"))
        db.add(user); db.commit(); db.refresh(user)

    eval_cases = [
        # (label, resume, jd, expected_min, expected_max)
        ("高匹配·同岗位", "Python后端5年 FastAPI Django Docker K8s 微服务 MySQL Redis 硕士", "高级Python后端 精通FastAPI Docker K8s", 75, 100),
        ("中匹配·跨方向", "数据分析3年 Python Pandas SQL Tableau", "Python后端 FastAPI Django MySQL Docker", 30, 65),
        ("弱匹配·不相关", "嵌入式MCU C++ ARM STM32 传感器", "Python后端 FastAPI RAG Agent LLM", 0, 30),
        ("极弱·信息不足", "技能：Python SQL Git", "高级后端 5年 Python Django Docker K8s 团队管理", 0, 20),
    ]

    service = GraphAnalysisService()
    hits = 0
    total = 0

    for label, resume, jd, lo, hi in eval_cases * 2:
        result = service.analyze(db, resume, jd, user.id, session_id="")
        if lo <= result.match_score <= hi:
            hits += 1
        total += 1

    db.close()
    return BenchResult(
        name="Match Score Accuracy",
        accuracy=round(hits / total, 3) if total else 0,
        total=total,
        details=[{"hit_rate": f"{hits}/{total}"}],
    )


# ── Benchmark 3: Guard Detection Rate ──

def bench_guard():
    """Test IntegrityGuard detection rate."""
    from app.guards.integrity_guard import IntegrityGuard

    guard = IntegrityGuard()
    cases = [
        # (label, resume, suggestions, expected_severity)
        ("编造指标", "Python开发参与后端项目",
         [{"suggestion": "实现了50%的性能提升", "grounded_in": "后端项目", "original": ""}], "risk"),
        ("编造技能", "Python开发做过网站",
         [{"suggestion": "添加Django和PostgreSQL精通", "grounded_in": "Python开发", "original": ""}], "risk"),
        ("夸大职责", "参与公司内部管理系统开发",
         [{"suggestion": "独立主导公司内部管理系统开发", "grounded_in": "参与", "original": "参与"}], "warning"),
        ("诚实建议", "Python后端5年，精通Django FastAPI",
         [{"suggestion": "突出Django和FastAPI的项目经验", "grounded_in": "精通Django、FastAPI", "original": ""}], "pass"),
        ("精通过多", "Python开发工程师",
         [{"suggestion": "精通Python Java C++ Go Rust K8s", "grounded_in": "Python开发", "original": ""}], "warning"),
    ]

    hits = 0
    total = len(cases)
    for label, resume, suggestions, expected in cases:
        result = guard.check(resume, suggestions)
        sevs = {f.severity for f in result.findings}
        if expected in sevs or (expected == "pass" and result.passed):
            hits += 1

    return BenchResult(
        name="Guard Detection Rate",
        accuracy=round(hits / total, 3),
        total=total,
        details=[{"detection_rate": f"{hits}/{total}"}],
    )


# ── Benchmark 4: NLP Scorer Speed ──

def bench_nlp_speed():
    """Measure NLP scorer throughput."""
    from app.services.nlp_scorer import NLPScorer

    scorer = NLPScorer()
    resume = "Python FastAPI Docker 5年经验 " * 5
    jd = "高级Python工程师 FastAPI Docker K8s 微服务 " * 3

    times = []
    for _ in range(20):
        t0 = time.time()
        scorer.score(resume, jd)
        times.append(time.time() - t0)

    return BenchResult(
        name="NLP Scorer (TF-IDF + Keyword)",
        latency_avg=round(np.mean(times) * 1000, 1),  # ms
        latency_p50=round(np.percentile(times, 50) * 1000, 1),
        latency_p95=round(np.percentile(times, 95) * 1000, 1),
        total=20,
    )


# ── Main ──

def main():
    print("=" * 65)
    print("CareerPilot-AI Benchmark Report")
    print("=" * 65)

    results = []

    print("\n[1/4] Agent Pipeline Latency...")
    r = bench_latency()
    results.append(r)
    print(f"  Avg: {r.latency_avg}s | P50: {r.latency_p50}s | P95: {r.latency_p95}s | Errors: {r.errors}")

    print("\n[2/4] Match Score Accuracy...")
    r = bench_accuracy()
    results.append(r)
    print(f"  Accuracy: {r.accuracy:.0%} ({r.total} cases)")

    print("\n[3/4] Guard Detection Rate...")
    r = bench_guard()
    results.append(r)
    print(f"  Detection: {r.accuracy:.0%} ({r.total} cases)")

    print("\n[4/4] NLP Scorer Speed...")
    r = bench_nlp_speed()
    results.append(r)
    print(f"  Avg: {r.latency_avg}ms | P50: {r.latency_p50}ms")

    print("\n" + "=" * 65)
    print("Summary")
    print("=" * 65)
    for r in results:
        if r.name.startswith("Agent") or r.name.startswith("NLP"):
            print(f"  {r.name:<35s} {r.latency_avg}{'s' if r.latency_avg > 1 else 'ms'} avg")
        else:
            print(f"  {r.name:<35s} {r.accuracy:.0%} accuracy")


if __name__ == "__main__":
    main()
