"""
Graph-based analysis service using LangGraph workflow.
Replaces the single-shot LLM call with a multi-step agent graph.
"""
import logging

from sqlalchemy.orm import Session

from app.agents.graph import build_graph
from app.agents.nodes import compose_report, fallback_rule
from app.agents.state import CareerPilotState
from app.core.errors import InputInsufficientError
from app.schemas.analysis import (
    IntegrityCheckItem,
    JDMatchResponse,
    KeywordCoverage,
    SkillGap,
    SuggestionItem,
)

logger = logging.getLogger(__name__)

MIN_RESUME_CHARS = 50
MIN_JD_CHARS = 30


class GraphAnalysisService:
    """JD matching powered by LangGraph agent workflow."""

    def __init__(self):
        self._graph = build_graph()

    def analyze(self, db: Session, resume_text: str, jd_text: str, user_id: int,
                session_id: str = "") -> JDMatchResponse:
        # Input validation
        if len(resume_text.strip()) < MIN_RESUME_CHARS:
            raise InputInsufficientError(
                f"简历内容过短（{len(resume_text.strip())} 字符），"
                f"请至少提供 {MIN_RESUME_CHARS} 字符，包含技能和工作经历。"
            )
        if len(jd_text.strip()) < MIN_JD_CHARS:
            raise InputInsufficientError(
                f"JD 内容过短（{len(jd_text.strip())} 字符），"
                f"请至少提供 {MIN_JD_CHARS} 字符的岗位描述。"
            )

        # Build initial state
        state: CareerPilotState = {
            "resume_text": resume_text,
            "jd_text": jd_text,
            "user_id": user_id,
            "session_id": session_id,
            "parsed_jd": None,
            "parsed_resume": None,
            "rule_match_score": 0,
            "llm_match_result": None,
            "guard_passed": False,
            "guard_findings": [],
            "guard_retry_count": 0,
            "max_guard_retries": 2,
            "final_report_id": None,
            "degraded": False,
            "degraded_reason": "",
            "progress_log": [],
            "error": None,
        }

        # Run the graph (stops at compose or fallback nodes)
        final_state = self._graph.invoke(state)

        # Handle terminal nodes that need db access
        if final_state.get("degraded") or final_state.get("error"):
            final_state = fallback_rule(final_state, db)
        else:
            final_state = compose_report(final_state, db)

        # Build response
        return self._build_response(final_state)

    def _build_response(self, state: CareerPilotState) -> JDMatchResponse:
        result = state.get("llm_match_result")

        if result is None:
            return JDMatchResponse(
                id=state.get("final_report_id"),
                match_score=state.get("rule_match_score", 0),
                degraded=True,
                degraded_reason=state.get("degraded_reason", ""),
                progress_log=state.get("progress_log", []),
            )

        skill_gaps = [
            SkillGap(skill=g.skill, required=g.required, user_has=g.user_has,
                     note=f"{g.depth_match}: {g.note}" if g.depth_match else g.note)
            for g in result.skill_gaps
        ]
        keyword_coverage = [
            KeywordCoverage(keyword=item.get("keyword", ""),
                           in_resume=item.get("in_resume", False),
                           in_jd=item.get("in_jd", True))
            for item in result.keyword_coverage
        ]
        suggestions = [
            SuggestionItem(category=s.category, original=s.original,
                           suggestion=f"[{s.confidence}] {s.suggestion}"
                           + (f" (依据: {s.grounded_in})" if s.grounded_in else ""),
                           confidence=s.confidence)
            for s in result.suggestions
        ]
        integrity_checks = [
            IntegrityCheckItem(severity=c.severity, category=c.category,
                               description=c.description, detail=c.detail)
            for c in result.integrity_checks
        ]

        return JDMatchResponse(
            id=state.get("final_report_id"),
            match_score=result.match_score,
            skill_gaps=skill_gaps,
            keyword_coverage=keyword_coverage,
            suggestions=suggestions,
            integrity_checks=integrity_checks,
            jd_summary=result.jd_summary,
            resume_summary=result.resume_summary,
            revised_resume=result.revised_resume,
            degraded=state.get("degraded", False),
            degraded_reason=state.get("degraded_reason", ""),
            progress_log=state.get("progress_log", []),
        )
