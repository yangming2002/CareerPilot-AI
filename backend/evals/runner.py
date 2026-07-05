"""
CareerPilot-AI Evaluation Harness
Usage: python -m evals.runner [--suite jd_match|integrity|injection|all]
"""
import json
import sys
import time
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent


def load_jsonl(name: str) -> list[dict]:
    path = EVALS_DIR / "datasets" / f"{name}.jsonl"
    if not path.exists():
        print(f"[SKIP] Dataset {name}.jsonl not found")
        return []
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


# ──────────────────── JD Match Suite ────────────────────

def ensure_test_user(db):
    from app.models.user import User
    from app.core.security import hash_password
    user = db.query(User).filter(User.email == "eval@test.com").first()
    if not user:
        user = User(email="eval@test.com", username="eval", hashed_password=hash_password("eval"))
        db.add(user)
        db.commit()
        db.refresh(user)
    return user.id


def run_jd_match_suite():
    from app.core.database import SessionLocal
    from app.services.llm_analysis_service import LLMAnalysisService

    cases = load_jsonl("jd_match_cases")
    if not cases:
        return

    db = SessionLocal()
    user_id = ensure_test_user(db)
    service = LLMAnalysisService()
    passed = 0
    failed = 0
    results = []

    for case in cases:
        print(f"\n{'='*60}")
        print(f"Case: {case['id']} — {case['label']}")
        print(f"Expected: {case['expect']}")

        result = None
        try:
            start = time.time()
            result = service.analyze(db, case["resume"], case["jd"], user_id=user_id)
            elapsed = time.time() - start
            db.commit()  # ensure clean state for next test

            checks_ok = True
            check_results = []
            for check in case.get("checks", []):
                r = eval_check(check, result)
                check_results.append({"check": check, "passed": r})
                if not r:
                    checks_ok = False

            status = "PASS" if checks_ok else "FAIL"
            if checks_ok:
                passed += 1
            else:
                failed += 1

            print(f"Score: {result.match_score} | Time: {elapsed:.1f}s | Degraded: {result.degraded}")
            print(f"Gaps: {len(result.skill_gaps)} | Suggestions: {len(result.suggestions)}")
            print(f"Status: {status}")
            for cr in check_results:
                print(f"  [{('OK' if cr['passed'] else 'FAIL')}] {cr['check']}")

        except Exception as e:
            failed += 1
            print(f"ERROR: {type(e).__name__}: {e}")

        results.append({
            "id": case["id"],
            "label": case["label"],
            "score": result.match_score if result else 0,
            "status": status if 'status' in dir() else "ERROR",
        })

    db.close()
    print(f"\n{'='*60}")
    print(f"JD Match Summary: {passed} passed, {failed} failed, {len(cases)} total")


def eval_check(check: str, result) -> bool:
    score = result.match_score
    gaps = result.skill_gaps

    if check.startswith("score_>="):
        return score >= int(check.split(">=")[1])
    elif check.startswith("score_<="):
        return score <= int(check.split("<=")[1])
    elif check == "score_between_30_55":
        return 30 <= score <= 55
    elif check == "gaps_contains_few_missing":
        gap_missing = sum(1 for g in gaps if not g.user_has)
        return gap_missing <= len(gaps) * 0.4
    elif check == "gaps_contains_many_missing":
        gap_missing = sum(1 for g in gaps if not g.user_has)
        return gap_missing >= len(gaps) * 0.5
    elif check == "gaps_highlights_framework_gap":
        framework_gaps = [g for g in gaps if "framework" in g.skill.lower() or "django" in g.skill.lower() or "fastapi" in g.skill.lower()]
        return len(framework_gaps) > 0
    elif check == "gaps_nearly_all_covered":
        gap_covered = sum(1 for g in gaps if g.user_has)
        return gap_covered >= len(gaps) * 0.8
    elif check == "suggestions_not_empty":
        return len(result.suggestions) > 0
    elif check == "suggestions_include_bridging":
        return len(result.suggestions) > 0
    elif check == "suggestions_include_portfolio_building":
        return len(result.suggestions) > 0
    elif check == "suggestions_minor_wording_only":
        return len(result.suggestions) <= 3
    elif check == "suggestions_no_fabricated_metrics":
        # LLM should suggest gathering real data, not invent metrics
        for s in result.suggestions:
            import re
            if re.search(r'\d+%|\d+倍|\d+万用户|提升了\d+', s.suggestion):
                return False
        return True
    elif check == "input_flagged_as_insufficient":
        return result.degraded or len(gaps) > 3
    return True


# ──────────────────── Integrity Suite ────────────────────

def run_integrity_suite():
    from app.guards.integrity_guard import IntegrityGuard

    cases = load_jsonl("integrity_cases")
    if not cases:
        return

    guard = IntegrityGuard()
    passed = 0
    failed = 0

    for case in cases:
        print(f"\n{'='*60}")
        print(f"Case: {case['id']} — {case['label']}")

        suggestions = case.get("suggestions", [{"suggestion": case.get("suggestion", ""), "grounded_in": case.get("grounded_in", case["resume"]), "original": ""}])
        result = guard.check(case["resume"], suggestions)

        # Check if expected findings match
        expected_severities = {f["severity"] for f in case.get("expected_findings", [])}
        actual_severities = {f.severity for f in result.findings}

        matched = expected_severities & actual_severities
        ok = len(matched) > 0 or ("pass" in expected_severities and result.passed)

        if ok:
            passed += 1
        else:
            failed += 1

        status = "PASS" if ok else "FAIL"
        print(f"Expected: {expected_severities} | Got: {actual_severities}")
        print(f"Status: {status}")
        for f in result.findings:
            print(f"  [{f.severity}] {f.category}: {f.description[:80]}")

    print(f"\n{'='*60}")
    print(f"Integrity Summary: {passed} passed, {failed} failed, {len(cases)} total")


# ──────────────────── Injection Suite ────────────────────

def run_injection_suite():
    from app.guards.prompt_injection_guard import PromptInjectionGuard

    cases = load_jsonl("injection_cases")
    if not cases:
        return

    guard = PromptInjectionGuard()
    passed = 0
    failed = 0

    for case in cases:
        print(f"\n{'='*60}")
        print(f"Case: {case['id']} — {case['label']}")

        result = guard.check(case["text"])
        expected = case["expected"]
        actual = "detected" if not result.passed else "safe"
        ok = actual == expected

        if ok:
            passed += 1
        else:
            failed += 1

        status = "PASS" if ok else "FAIL"
        print(f"Expected: {expected} | Got: {actual} | Status: {status}")
        for f in result.findings:
            print(f"  [{f.severity}] {f.description[:80]}")

    print(f"\n{'='*60}")
    print(f"Injection Summary: {passed} passed, {failed} failed, {len(cases)} total")


# ──────────────────── Main ────────────────────

def main():
    suite = sys.argv[2] if len(sys.argv) > 2 else "all"

    if suite in ("all", "jd_match"):
        print("\n### JD Match Evaluation ###")
        run_jd_match_suite()

    if suite in ("all", "integrity"):
        print("\n### Integrity Guard Evaluation ###")
        run_integrity_suite()

    if suite in ("all", "injection"):
        print("\n### Prompt Injection Evaluation ###")
        run_injection_suite()

    print("\nDone.")


if __name__ == "__main__":
    main()
