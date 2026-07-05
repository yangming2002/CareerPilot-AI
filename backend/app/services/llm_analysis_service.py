import hashlib
from typing import Callable

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

from loguru import logger

MIN_RESUME_CHARS = 50
MIN_JD_CHARS = 30
MAX_GUARD_RETRIES = 1


class LLMAnalysisService:
    def __init__(self):
        self.guard_runner = GuardRunner()
        self._progress: list[str] = []

    def _log(self, msg: str) -> None:
        logger.info(f"[LLM] {msg}")
        logger.info(msg)
        self._progress.append(msg)

    def analyze(self, db: Session, resume_text: str, jd_text: str, user_id: int) -> JDMatchResponse:
        self._progress = []

        # ── 1. Input check ──
        self._log("检查简历和 JD 内容...")
        self._validate_input(resume_text, jd_text)

        # ── 2. Injection scan ──
        self._log("检查输入安全性...")
        jd_check = self.guard_runner.check_input(jd_text, "JD")
        if not jd_check.passed:
            self._log("JD 包含可疑内容，降级为规则引擎")
            return self._build_degraded(db, resume_text, jd_text, user_id,
                                        "JD 内容包含疑似指令注入，已使用规则引擎分析。", match_score=0)

        # ── 3. LLM call ──
        self._log("正在调用 LLM 分析，请稍候...")
        llm = get_llm_client()
        user_prompt = JD_MATCH_USER.format(jd_text=jd_text, resume_text=resume_text)
        result: LLMMatchResult | None = None

        for attempt in range(MAX_GUARD_RETRIES + 1):
            label = "正在深度分析..." if attempt == 0 else f"正在根据校验反馈重新优化 (第 {attempt} 次)..."
            self._log(label)

            try:
                result = llm.complete_structured(
                    system=JD_MATCH_SYSTEM,
                    user=user_prompt,
                    output_schema=LLMMatchResult,
                )
            except (APITimeoutError, APIConnectionError):
                self._log("LLM 连接超时，切换为规则引擎分析")
                return self._build_degraded(db, resume_text, jd_text, user_id,
                                            "LLM 服务连接超时，已自动切换为规则引擎分析。", match_score=None)
            except Exception as e:
                self._log(f"LLM 调用异常: {e}")
                if attempt < MAX_GUARD_RETRIES:
                    continue
                return self._build_degraded(db, resume_text, jd_text, user_id,
                                            f"LLM 分析失败，已自动切换为规则引擎分析。", match_score=None)

            self._log(f"分析完成 (匹配分 {result.match_score}, "
                      f"技能缺口 {len(result.skill_gaps)} 项, 建议 {len(result.suggestions)} 条)")

            # Guards
            if attempt < MAX_GUARD_RETRIES:
                self._log("正在校验建议真实性...")
                runner_result = self.guard_runner.run(resume_text, [
                    s.model_dump() for s in result.suggestions
                ])
                if runner_result.passed:
                    self._log("真实性校验通过")
                    break
                else:
                    risk_count = sum(1 for r in runner_result.results for f in r.findings if f.severity == "risk")
                    self._log(f"发现 {risk_count} 个风险项，正在重新生成...")
                    hints = "\n".join(runner_result.combined_hints)
                    user_prompt = (
                        JD_MATCH_USER.format(jd_text=jd_text, resume_text=resume_text)
                        + f"\n\n## 上次输出的问题（请修正）\n{hints}"
                    )
            else:
                self._log("已达最大重试次数，使用当前结果")

        if result is None:
            self._log("未能获取有效结果，降级为规则引擎")
            return self._build_degraded(db, resume_text, jd_text, user_id,
                                        "LLM 未能生成有效分析结果。", match_score=None)

        # ── 4. Save ──
        self._log("正在保存报告...")
        response = self._build_response(db, resume_text, jd_text, result, user_id)
        self._log("完成!")
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
        keyword_coverage: list[KeywordCoverage] = []
        suggestions = [
            SuggestionItem(category=s.category, original=s.original,
                           suggestion=s.suggestion,
                           confidence=s.confidence,
                           grounded_in=s.grounded_in)
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
            progress_log=self._progress,
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
            result.progress_log = self._progress
            return result

        return JDMatchResponse(
            id=None, match_score=match_score, skill_gaps=[],
            keyword_coverage=[], suggestions=[], integrity_checks=[
                IntegrityCheckItem(severity="warning", category="system",
                                   description=reason, detail="")
            ],
            jd_summary=jd_text[:120], resume_summary=resume_text[:120],
            degraded=True, degraded_reason=reason,
            progress_log=self._progress,
        )
