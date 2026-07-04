import hashlib
import logging
import sys

from openai import APITimeoutError, APIConnectionError
from sqlalchemy.orm import Session

from app.core.errors import InputInsufficientError
from app.guards.guard_runner import GuardRunner
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

MIN_RESUME_CHARS = 50
MIN_JD_CHARS = 30
MAX_GUARD_RETRIES = 1  # reduced: 1 initial + 1 retry = max 2 LLM calls


def _log(msg: str) -> None:
    """Print to stderr so it shows in uvicorn console immediately."""
    print(f"[LLM] {msg}", file=sys.stderr, flush=True)
    logger.info(msg)


class LLMAnalysisService:
    def __init__(self):
        self.guard_runner = GuardRunner()

    def analyze(self, db: Session, resume_text: str, jd_text: str, user_id: int) -> JDMatchResponse:
        # ── 1. Input check ──
        _log("步骤 1/4: 检查输入...")
        self._validate_input(resume_text, jd_text)
        _log(f"  输入长度 OK (简历 {len(resume_text)} 字, JD {len(jd_text)} 字)")

        # ── 2. Injection scan ──
        _log("步骤 2/4: 安全检查...")
        jd_check = self.guard_runner.check_input(jd_text, "JD")
        if not jd_check.passed:
            _log("  JD 包含疑似注入，降级到规则引擎")
            return self._build_degraded(db, resume_text, jd_text, user_id,
                                        "JD 内容包含疑似指令注入，已使用规则引擎分析。", match_score=0)

        # ── 3. LLM call + guard ──
        _log("步骤 3/4: 调用 LLM 分析...")
        llm = get_llm_client()
        user_prompt = JD_MATCH_USER.format(jd_text=jd_text, resume_text=resume_text)
        result: LLMMatchResult | None = None

        for attempt in range(MAX_GUARD_RETRIES + 1):
            label = "初次调用" if attempt == 0 else f"Guard 重试 ({attempt}/{MAX_GUARD_RETRIES})"
            _log(f"  {label}...")

            try:
                result = llm.complete_structured(
                    system=JD_MATCH_SYSTEM,
                    user=user_prompt,
                    output_schema=LLMMatchResult,
                )
            except (APITimeoutError, APIConnectionError):
                _log("  连接失败，降级到规则引擎")
                return self._build_degraded(db, resume_text, jd_text, user_id,
                                            "LLM 服务连接超时，已自动切换为规则引擎分析。", match_score=None)
            except Exception as e:
                _log(f"  调用异常: {e}")
                if attempt < MAX_GUARD_RETRIES:
                    continue
                return self._build_degraded(db, resume_text, jd_text, user_id,
                                            f"LLM 分析失败：{e}。已自动切换为规则引擎分析。", match_score=None)

            _log(f"  返回匹配分: {result.match_score}, 技能缺口: {len(result.skill_gaps)}, "
                 f"建议: {len(result.suggestions)}")

            # Run guards (GroundingGuard is advisory-only, IntegrityGuard can block)
            if attempt < MAX_GUARD_RETRIES:
                runner_result = self.guard_runner.run(resume_text, [
                    s.model_dump() for s in result.suggestions
                ])
                if runner_result.passed:
                    _log("  Guard 检查通过")
                    break
                else:
                    _log(f"  Guard 发现问题，反馈给 LLM 重写...")
                    hints = "\n".join(runner_result.combined_hints)
                    user_prompt = (
                        JD_MATCH_USER.format(jd_text=jd_text, resume_text=resume_text)
                        + f"\n\n## 上次输出的问题（请修正）\n{hints}"
                    )
            else:
                _log("  已达最大重试次数，使用当前结果")

        if result is None:
            _log("  无有效结果，降级")
            return self._build_degraded(db, resume_text, jd_text, user_id,
                                        "LLM 未能生成有效分析结果，已自动切换为规则引擎。", match_score=None)

        # ── 4. Save ──
        _log("步骤 4/4: 保存报告...")
        response = self._build_response(db, resume_text, jd_text, result, user_id)
        _log(f"完成! 匹配分={response.match_score}, 降级={response.degraded}")
        return response

    def _validate_input(self, resume_text: str, jd_text: str) -> None:
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

    def _build_response(
        self, db: Session, resume_text: str, jd_text: str,
        result: LLMMatchResult, user_id: int,
    ) -> JDMatchResponse:
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
            id=report.id, match_score=result.match_score,
            skill_gaps=skill_gaps, keyword_coverage=keyword_coverage,
            suggestions=suggestions, integrity_checks=integrity_checks,
            jd_summary=result.jd_summary, resume_summary=result.resume_summary,
        )

    def _build_degraded(
        self, db: Session, resume_text: str, jd_text: str,
        user_id: int, reason: str, match_score: int | None,
    ) -> JDMatchResponse:
        from app.services.analysis_service import AnalysisService

        if match_score is None:
            result = AnalysisService().analyze(db, resume_text, jd_text, user_id)
            result.degraded = True
            result.degraded_reason = reason
            return result

        return JDMatchResponse(
            id=None, match_score=match_score, skill_gaps=[],
            keyword_coverage=[], suggestions=[], integrity_checks=[
                IntegrityCheckItem(severity="warning", category="system",
                                   description=reason, detail="")
            ],
            jd_summary=jd_text[:120], resume_summary=resume_text[:120],
            degraded=True, degraded_reason=reason,
        )
