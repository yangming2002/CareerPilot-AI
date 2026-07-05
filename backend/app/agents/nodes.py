"""Node functions for the CareerPilot LangGraph workflow."""
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session

from app.agents.state import CareerPilotState
from app.guards.guard_runner import GuardRunner
from app.llm.client import LLMClient, LLMConfig
from app.llm.prompts import JD_MATCH_SYSTEM, JD_MATCH_USER
from app.llm.schemas import LLMMatchResult, ParsedJD, ParsedResumeFields
from app.models.models import AnalysisReport

from loguru import logger
MAX_GUARD_RETRIES = 2

# Turbo for all LLM calls — plus is 10x slower for minimal quality gain
_parse_client = LLMClient(LLMConfig(model="qwen-turbo", max_tokens=1024))
_analysis_client = LLMClient(LLMConfig(model="qwen-turbo", max_tokens=4096, timeout=60))


def parse_both(state: CareerPilotState) -> CareerPilotState:
    """Run JD and resume parsing in parallel. Cached by text hash."""
    state.setdefault("progress_log", [])
    t0 = time.time()

    jd_hash = _text_hash(state["jd_text"])
    resume_hash = _text_hash(state["resume_text"])

    # Check cache
    if jd_hash in _PARSE_CACHE:
        state["parsed_jd"] = _PARSE_CACHE[jd_hash]
    if resume_hash in _PARSE_CACHE:
        state["parsed_resume"] = _PARSE_CACHE[resume_hash]

    if state.get("parsed_jd") and state.get("parsed_resume"):
        _log(state, "  JD+简历解析 (缓存命中)", time.time() - t0)
        return state

    with ThreadPoolExecutor(max_workers=2) as pool:
        if not state.get("parsed_jd"):
            pool.submit(_parse_jd_impl, state)
        if not state.get("parsed_resume"):
            pool.submit(_parse_resume_impl, state)

    # Store in cache
    if state.get("parsed_jd"):
        _PARSE_CACHE[jd_hash] = state["parsed_jd"]
    if state.get("parsed_resume"):
        _PARSE_CACHE[resume_hash] = state["parsed_resume"]

    _log(state, "  JD+简历解析 (并行)", time.time() - t0)
    return state


_PARSE_CACHE: dict[str, object] = {}


def _text_hash(text: str) -> str:
    import hashlib
    return hashlib.md5(text.encode()).hexdigest()


def _parse_resume_impl(state: CareerPilotState) -> None:
    from app.llm.prompts import RESUME_PARSE_SYSTEM, RESUME_PARSE_USER
    from app.llm.schemas import ParsedResumeFields
    try:
        # Truncate to prevent slow parsing on very long resumes
        resume_short = state["resume_text"][:2000]
        result = _parse_client.complete_structured(
            system=RESUME_PARSE_SYSTEM,
            user=RESUME_PARSE_USER.format(resume_text=resume_short) + "\n(Please respond with a JSON object.)",
            output_schema=ParsedResumeFields,
        )
        state["parsed_resume"] = result
    except Exception:
        state["parsed_resume"] = ParsedResumeFields(raw_summary=state["resume_text"][:200])


def _parse_jd_impl(state: CareerPilotState) -> None:
    from app.llm.schemas import ParsedJD
    try:
        jd_short = state["jd_text"][:1500]
        result = _parse_client.complete_structured(
            system="Parse this job description. All output in Chinese.",
            user=f"Parse this JD:\n\n{jd_short}\n\n(Please respond with a JSON object.)",
            output_schema=ParsedJD,
        )
        state["parsed_jd"] = result
    except Exception:
        state["parsed_jd"] = ParsedJD(summary=state["jd_text"][:200])


def _log(state: CareerPilotState, msg: str, elapsed: float = 0) -> None:
    ts = f" ({elapsed:.1f}s)" if elapsed else ""
    full_msg = f"{msg}{ts}"
    logger.info(f"[Agent] {full_msg}")
    state.setdefault("progress_log", []).append(full_msg)
    sid = state.get("session_id", "")
    if sid:
        from app.core import progress as ps
        ps.push(sid, full_msg)


# ──────────── Node: parse_jd (turbo, fast) ────────────

def parse_jd(state: CareerPilotState) -> CareerPilotState:
    t0 = time.time()
    try:
        result = _parse_client.complete_structured(
            system="Parse this job description. All output in Chinese.",
            user=f"Parse this JD:\n\n{state['jd_text']}\n\n(Please respond with a JSON object.)",
            output_schema=ParsedJD,
        )
        state["parsed_jd"] = result
    except Exception:
        state["parsed_jd"] = ParsedJD(summary=state["jd_text"][:200])
    _log(state, "  JD 解析 (turbo)", time.time() - t0)
    return state


# ──────────── Node: parse_resume (turbo, fast) ────────────

def parse_resume(state: CareerPilotState) -> CareerPilotState:
    t0 = time.time()
    from app.llm.prompts import RESUME_PARSE_SYSTEM, RESUME_PARSE_USER
    try:
        result = _parse_client.complete_structured(
            system=RESUME_PARSE_SYSTEM,
            user=RESUME_PARSE_USER.format(resume_text=state["resume_text"]) + "\n(Please respond with a JSON object.)",
            output_schema=ParsedResumeFields,
        )
        state["parsed_resume"] = result
    except Exception:
        state["parsed_resume"] = ParsedResumeFields(raw_summary=state["resume_text"][:200])
    _log(state, "  简历解析 (turbo)", time.time() - t0)
    return state


# ──────────── Node: rule_match ────────────

def rule_match(state: CareerPilotState) -> CareerPilotState:
    t0 = time.time()
    from app.services.analysis_service import AnalysisService
    service = AnalysisService()
    jd_skills = service._extract_skills(state["jd_text"].lower())
    resume_skills = service._extract_skills(state["resume_text"].lower())
    gaps = service._compute_skill_gaps(jd_skills, resume_skills)
    score = service._compute_score(jd_skills, resume_skills, gaps)
    state["rule_match_score"] = score
    _log(state, "  规则引擎评分", time.time() - t0)
    return state


# ──────────── Node: llm_analysis (plus, quality) ────────────

def llm_analysis(state: CareerPilotState) -> CareerPilotState:
    t0 = time.time()

    # Retrieve relevant facts from memory (skip if no facts exist yet)
    from app.memory.retriever import FactRetriever
    from app.memory.models import UserFact
    from app.core.database import SessionLocal
    memory_db = SessionLocal()
    memory_context = {"relevant_skills": [], "relevant_projects": [], "past_weaknesses": [], "similar_jds": [], "user_profile": {}}
    try:
        fact_count = memory_db.query(UserFact).filter(UserFact.user_id == state["user_id"]).count()
        if fact_count > 0:
            retriever = FactRetriever()
            jd_skills = [g["skill"] for g in state.get("llm_match_result", {}).get("skill_gaps", [])] if state.get("llm_match_result") else []
            memory_context = retriever.retrieve_for_jd(
                memory_db, state["user_id"], state["jd_text"], jd_skills, limit=8
            )
    finally:
        memory_db.close()

    memory_text = ""
    if memory_context["relevant_skills"]:
        memory_text += "\n## 你的相关技能（来自历史记录）\n"
        for s in memory_context["relevant_skills"][:5]:
            memory_text += f"- {s['content']}\n"
    if memory_context["relevant_projects"]:
        memory_text += "\n## 你的相关项目经历\n"
        for p in memory_context["relevant_projects"][:5]:
            memory_text += f"- {p['content'][:200]}\n"

    _log(state, f"  检索: {len(memory_context['relevant_skills'])}技能 {len(memory_context['relevant_projects'])}项目", time.time() - t0)
    t1 = time.time()

    extra = ""
    if state.get("guard_retry_count", 0) > 0:
        hints = "\n".join(
            f.get("description", "") for f in state.get("guard_findings", []) if f.get("severity") == "risk"
        )
        extra = f"\n\n## 上次输出被真实性校验驳回，请修正以下问题：\n{hints}"

    user_prompt = JD_MATCH_USER.format(
        jd_text=state["jd_text"],
        resume_text=state["resume_text"],
    ) + memory_text + extra + "\n(Please respond with a JSON object.)"

    # --- LLM call with detailed timing ---
    import json
    t_build = time.time()
    structured_system = (
        JD_MATCH_SYSTEM
        + f"\n\nYou MUST respond with a single JSON object matching this schema:\n```json\n{json.dumps(LLMMatchResult.model_json_schema(), ensure_ascii=False, indent=2)}\n```\n"
        + "Reply ONLY with the JSON object, no markdown fences, no extra text."
    )
    prompt_chars = len(structured_system) + len(user_prompt)
    _log(state, f"  Prompt构建 ({prompt_chars}字, schema={len(LLMMatchResult.model_json_schema()['properties'])}字段)", time.time() - t_build)

    t_call = time.time()
    try:
        result = _analysis_client.complete_structured(
            system=JD_MATCH_SYSTEM,
            user=user_prompt,
            output_schema=LLMMatchResult,
        )
        state["llm_match_result"] = result
        _log(state, f"  API调用+推理", time.time() - t_call)
    except Exception as e:
        logger.exception("LLM analysis failed")
        state["error"] = str(e)
        state["degraded"] = True
        state["degraded_reason"] = f"LLM 分析失败: {e}"

    _log(state, f"  LLM 匹配总计 (turbo)", time.time() - t1)
    return state


# ──────────── Node: integrity_guard ────────────

def integrity_guard(state: CareerPilotState) -> CareerPilotState:
    t0 = time.time()
    runner = GuardRunner()
    result = state.get("llm_match_result")
    if result is None:
        state["guard_passed"] = False
        return state

    suggestions = [s.model_dump() for s in result.suggestions]
    runner_result = runner.run(state["resume_text"], suggestions)
    state["guard_passed"] = runner_result.passed
    state["guard_findings"] = [f for r in runner_result.results for f in r.findings]
    state["guard_retry_count"] = state.get("guard_retry_count", 0) + 1
    _log(state, "  真实性校验", time.time() - t0)
    return state


# ──────────── Node: compose_report ────────────

def compose_report(state: CareerPilotState, db: Session) -> CareerPilotState:
    t0 = time.time()
    result = state.get("llm_match_result")
    if result is None:
        state["degraded"] = True
        state["degraded_reason"] = "LLM 未生成有效结果"
        return state

    resume_hash = hashlib.sha256(state["resume_text"].encode()).hexdigest()
    jd_hash = hashlib.sha256(state["jd_text"].encode()).hexdigest()

    report = AnalysisReport(
        user_id=state["user_id"],
        resume_text_hash=resume_hash,
        jd_text_hash=jd_hash,
        match_score=result.match_score,
        skill_gaps=[g.model_dump() for g in result.skill_gaps],
        keyword_coverage=[],
        suggestions=[s.model_dump() for s in result.suggestions],
        integrity_checks=[c.model_dump() for c in result.integrity_checks],
        raw_jd_summary=result.jd_summary,
        raw_resume_summary=result.resume_summary,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    state["final_report_id"] = report.id
    state["degraded"] = False
    _log(state, f"  汇总保存 (ID={report.id})", time.time() - t0)
    return state


# ──────────── Node: fallback_rule ────────────

def fallback_rule(state: CareerPilotState, db: Session) -> CareerPilotState:
    from app.services.analysis_service import AnalysisService
    service = AnalysisService()
    result = service.analyze(db, state["resume_text"], state["jd_text"], state["user_id"])
    state["final_report_id"] = result.id
    state["rule_match_score"] = result.match_score
    state["degraded"] = True
    state["degraded_reason"] = "LLM 服务不可用，已使用规则引擎分析"
    return state
