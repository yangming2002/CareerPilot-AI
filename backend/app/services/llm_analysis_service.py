import hashlib
import logging

from sqlalchemy.orm import Session

from app.llm.client import get_llm_client
from app.llm.prompts import JD_MATCH_SYSTEM, JD_MATCH_USER
from app.llm.schemas import LLMMatchResult
from app.models.models import AnalysisReport
from app.schemas.analysis import (
    IntegrityCheckItem,
    JDMatchResponse,
    KeywordCoverage,
    SkillGap,
    SuggestionItem,
)

logger = logging.getLogger(__name__)


class LLMAnalysisService:
    """JD-Resume matching powered by OpenAI LLM with structured output."""

    def analyze(self, db: Session, resume_text: str, jd_text: str, user_id: int) -> JDMatchResponse:
        llm = get_llm_client()

        user_prompt = JD_MATCH_USER.format(
            jd_text=jd_text,
            resume_text=resume_text,
        )

        result = llm.complete_structured(
            system=JD_MATCH_SYSTEM,
            user=user_prompt,
            output_schema=LLMMatchResult,
        )

        if result is None:
            logger.warning("LLM structured output failed, returning fallback")
            return self._fallback_response(resume_text, jd_text)

        return self._build_response(db, resume_text, jd_text, result, user_id)

    # ──────────────── mapping to JDMatchResponse ────────────────

    def _build_response(
        self,
        db: Session,
        resume_text: str,
        jd_text: str,
        result: LLMMatchResult,
        user_id: int,
    ) -> JDMatchResponse:
        skill_gaps = [
            SkillGap(
                skill=g.skill,
                required=g.required,
                user_has=g.user_has,
                note=f"{g.depth_match}: {g.note}" if g.depth_match else g.note,
            )
            for g in result.skill_gaps
        ]

        keyword_coverage = [
            KeywordCoverage(
                keyword=item.get("keyword", ""),
                in_resume=item.get("in_resume", False),
                in_jd=item.get("in_jd", True),
            )
            for item in result.keyword_coverage
        ]

        suggestions = [
            SuggestionItem(
                category=s.category,
                original=s.original,
                suggestion=f"[{s.confidence}] {s.suggestion}" + (f" (依据: {s.grounded_in})" if s.grounded_in else ""),
                confidence=s.confidence,
            )
            for s in result.suggestions
        ]

        integrity_checks = [
            IntegrityCheckItem(
                severity=c.severity,
                category=c.category,
                description=c.description,
                detail=c.detail,
            )
            for c in result.integrity_checks
        ]

        resume_hash = hashlib.sha256(resume_text.encode()).hexdigest()
        jd_hash = hashlib.sha256(jd_text.encode()).hexdigest()

        report = AnalysisReport(
            user_id=user_id,
            resume_text_hash=resume_hash,
            jd_text_hash=jd_hash,
            match_score=result.match_score,
            skill_gaps=[g.model_dump() for g in skill_gaps],
            keyword_coverage=[k.model_dump() for k in keyword_coverage],
            suggestions=[s.model_dump() for s in suggestions],
            integrity_checks=[i.model_dump() for i in integrity_checks],
            raw_jd_summary=result.jd_summary,
            raw_resume_summary=result.resume_summary,
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return JDMatchResponse(
            id=report.id,
            match_score=result.match_score,
            skill_gaps=skill_gaps,
            keyword_coverage=keyword_coverage,
            suggestions=suggestions,
            integrity_checks=integrity_checks,
            jd_summary=result.jd_summary,
            resume_summary=result.resume_summary,
        )

    def _fallback_response(self, resume_text: str, jd_text: str) -> JDMatchResponse:
        return JDMatchResponse(
            id=None,
            match_score=0,
            skill_gaps=[],
            keyword_coverage=[],
            suggestions=[
                SuggestionItem(
                    category="system",
                    original="",
                    suggestion="LLM 分析暂时不可用，请稍后重试。规则引擎分析数据已就绪，可切换回规则模式。",
                    confidence="low",
                )
            ],
            integrity_checks=[
                IntegrityCheckItem(
                    severity="warning",
                    category="system",
                    description="LLM 结构化输出失败，返回降级结果",
                    detail="请检查 API Key 和网络连接",
                )
            ],
            jd_summary=jd_text[:120],
            resume_summary=resume_text[:120],
        )
