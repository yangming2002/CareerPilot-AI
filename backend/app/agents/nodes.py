"""Node functions for the CareerPilot LangGraph workflow."""
import hashlib
import logging
import sys

from sqlalchemy.orm import Session

from app.agents.state import CareerPilotState
from app.guards.guard_runner import GuardRunner
from app.llm.client import get_llm_client
from app.llm.prompts import (
    JD_MATCH_SYSTEM,
    JD_MATCH_USER,
    RESUME_PARSE_SYSTEM,
    RESUME_PARSE_USER,
    INTEGRITY_GUARD_SYSTEM,
    INTEGRITY_GUARD_USER,
)
from app.llm.schemas import LLMIntegrityCheck, LLMMatchResult, ParsedJD, ParsedResumeFields
from app.models.models import AnalysisReport

logger = logging.getLogger(__name__)
MAX_GUARD_RETRIES = 2


def _log(state: CareerPilotState, msg: str) -> None:
    print(f"[Agent] {msg}", file=sys.stderr, flush=True)
    state.setdefault("progress_log", []).append(msg)
    # Push to shared store for frontend polling
    sid = state.get("session_id", "")
    if sid:
        from app.core import progress as ps
        ps.push(sid, msg)


# ──────────── Node: parse_jd ────────────

def parse_jd(state: CareerPilotState) -> CareerPilotState:
    _log(state, "Agent: 解析 JD...")
    llm = get_llm_client()
    try:
        result = llm.complete_structured(
            system="Parse this job description into structured fields. All text in Chinese.",
            user=f"Parse this JD:\n\n{state['jd_text']}\n\n(Please respond with a JSON object.)",
            output_schema=ParsedJD,
        )
        state["parsed_jd"] = result
    except Exception as e:
        logger.exception("JD parsing failed")
        state["parsed_jd"] = ParsedJD(summary=state["jd_text"][:200])
    return state


# ──────────── Node: parse_resume ────────────

def parse_resume(state: CareerPilotState) -> CareerPilotState:
    _log(state, "Agent: 解析简历...")
    llm = get_llm_client()
    try:
        result = llm.complete_structured(
            system=RESUME_PARSE_SYSTEM,
            user=RESUME_PARSE_USER.format(resume_text=state["resume_text"]) + "\n(Please respond with a JSON object.)",
            output_schema=ParsedResumeFields,
        )
        state["parsed_resume"] = result
    except Exception as e:
        logger.exception("Resume parsing failed")
        state["parsed_resume"] = ParsedResumeFields(raw_summary=state["resume_text"][:200])
    return state


# ──────────── Node: rule_match ────────────

def rule_match(state: CareerPilotState) -> CareerPilotState:
    _log(state, "Agent: 规则引擎快速评分...")
    from app.services.analysis_service import AnalysisService
    service = AnalysisService()
    # Rule engine returns a JDMatchResponse, we just need the score
    jd_skills = service._extract_skills(state["jd_text"].lower())
    resume_skills = service._extract_skills(state["resume_text"].lower())
    gaps = service._compute_skill_gaps(jd_skills, resume_skills)
    score = service._compute_score(jd_skills, resume_skills, gaps)
    state["rule_match_score"] = score
    return state


# ──────────── Node: llm_analysis ────────────

def llm_analysis(state: CareerPilotState) -> CareerPilotState:
    _log(state, "Agent: 检索相关经历...")
    # Retrieve relevant user facts from memory
    from app.memory.retriever import FactRetriever
    from app.core.database import SessionLocal
    memory_db = SessionLocal()
    try:
        retriever = FactRetriever()
        jd_skills = [g["skill"] for g in state.get("llm_match_result", {}).get("skill_gaps", [])] if state.get("llm_match_result") else []
        memory_context = retriever.retrieve_for_jd(
            memory_db, state["user_id"], state["jd_text"], jd_skills, limit=8
        )
    finally:
        memory_db.close()

    # Build memory context for prompt
    memory_text = ""
    if memory_context["relevant_skills"]:
        memory_text += "\n## 你的相关技能（来自历史记录）\n"
        for s in memory_context["relevant_skills"][:5]:
            memory_text += f"- {s['content']}\n"
    if memory_context["relevant_projects"]:
        memory_text += "\n## 你的相关项目经历\n"
        for p in memory_context["relevant_projects"][:5]:
            memory_text += f"- {p['content'][:200]}\n"
    if memory_context["past_weaknesses"]:
        memory_text += "\n## 你过去的技能短板\n"
        for w in memory_context["past_weaknesses"]:
            memory_text += f"- {w.content[:100]}\n"

    _log(state, f"Agent: 检索到 {len(memory_context['relevant_skills'])} 个技能, "
         f"{len(memory_context['relevant_projects'])} 个项目")

    _log(state, "Agent: LLM 深度分析...")
    llm = get_llm_client()

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

    try:
        result = llm.complete_structured(
            system=JD_MATCH_SYSTEM,
            user=user_prompt,
            output_schema=LLMMatchResult,
        )
        state["llm_match_result"] = result
    except Exception as e:
        logger.exception("LLM analysis failed")
        state["error"] = str(e)
        state["degraded"] = True
        state["degraded_reason"] = f"LLM 分析失败: {e}"
    return state


# ──────────── Node: integrity_guard ────────────

def integrity_guard(state: CareerPilotState) -> CareerPilotState:
    _log(state, "Agent: 真实性校验...")
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
    return state


# ──────────── Node: compose_report ────────────

def compose_report(state: CareerPilotState, db: Session) -> CareerPilotState:
    _log(state, "Agent: 汇总报告...")
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
        keyword_coverage=result.keyword_coverage,
        suggestions=[s.model_dump() for s in result.suggestions],
        integrity_checks=[c.model_dump() for c in result.integrity_checks],
        raw_jd_summary=result.jd_summary,
        raw_resume_summary=result.resume_summary,
        revised_resume=result.revised_resume,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    state["final_report_id"] = report.id
    state["degraded"] = False
    _log(state, f"Agent: 报告已保存 (ID={report.id}, 匹配分={result.match_score})")
    return state


# ──────────── Node: fallback_rule ────────────

def fallback_rule(state: CareerPilotState, db: Session) -> CareerPilotState:
    _log(state, "Agent: LLM 不可用，降级为规则引擎...")
    from app.services.analysis_service import AnalysisService
    service = AnalysisService()
    result = service.analyze(db, state["resume_text"], state["jd_text"], state["user_id"])
    state["final_report_id"] = result.id
    state["rule_match_score"] = result.match_score
    state["degraded"] = True
    state["degraded_reason"] = "LLM 服务不可用，已使用规则引擎分析"
    return state
