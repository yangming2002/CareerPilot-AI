"""Rule-based analysis service — fast fallback when LLM is unavailable."""
import hashlib
import re

from sqlalchemy.orm import Session

from app.models.models import AnalysisReport
from app.schemas.analysis import (
    IntegrityCheckItem,
    JDMatchResponse,
    SkillGap,
    SuggestionItem,
)
from app.services.nlp_scorer import NLPScorer


class AnalysisService:
    """Fast rule-based matching. Uses NLP scorer for objective metrics."""

    def __init__(self):
        self._nlp = NLPScorer()

    def analyze(self, db: Session, resume_text: str, jd_text: str, user_id: int) -> JDMatchResponse:
        # NLP objective scoring
        scores = self._nlp.score(resume_text, jd_text)
        overlap = scores.get("skill_overlap", {})
        matched = overlap.get("matched", [])
        missing = overlap.get("missing", [])

        # Build skill gaps from overlap data
        skill_gaps = []
        for s in matched:
            skill_gaps.append(SkillGap(skill=s, required=True, user_has=True, note="已覆盖"))
        for s in missing:
            skill_gaps.append(SkillGap(skill=s, required=True, user_has=False,
                                       note="JD 要求但简历未明确提及"))

        # Score: 70% NLP + 30% density bonus
        density = min(1.0, len(resume_text.strip()) / 200)
        match_score = int(scores["keyword_coverage"] * 0.7 + density * 30)

        # Generate suggestions from gaps
        suggestions = self._suggestions(missing, resume_text)

        # Integrity checks
        integrity_checks = self._run_integrity_checks(resume_text)

        jd_summary = jd_text[:120] + ("..." if len(jd_text) > 120 else "")
        resume_summary = resume_text[:120] + ("..." if len(resume_text) > 120 else "")

        resume_hash = hashlib.sha256(resume_text.encode()).hexdigest()
        jd_hash = hashlib.sha256(jd_text.encode()).hexdigest()

        report = AnalysisReport(
            user_id=user_id,
            resume_text_hash=resume_hash,
            jd_text_hash=jd_hash,
            match_score=match_score,
            skill_gaps=[g.model_dump() for g in skill_gaps],
            keyword_coverage=[],
            suggestions=[s.model_dump() for s in suggestions],
            integrity_checks=[i.model_dump() for i in integrity_checks],
            raw_jd_summary=jd_summary,
            raw_resume_summary=resume_summary,
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return JDMatchResponse(
            id=report.id,
            match_score=match_score,
            skill_gaps=skill_gaps,
            keyword_coverage=[],
            suggestions=suggestions,
            integrity_checks=integrity_checks,
            jd_summary=jd_summary,
            resume_summary=resume_summary,
        )

    # Agent rule_match node still uses these for fast scoring
    def _extract_skills(self, text: str) -> set[str]:
        from app.services.nlp_scorer import NLPScorer
        return {kw for kw in NLPScorer._load_tech_keywords() if kw.lower() in text}

    def _compute_skill_gaps(self, jd_skills: set[str], resume_skills: set[str]) -> list[SkillGap]:
        gaps = []
        for s in sorted(jd_skills - resume_skills):
            gaps.append(SkillGap(skill=s, required=True, user_has=False, note="JD 要求但简历未明确提及"))
        for s in sorted(jd_skills & resume_skills):
            gaps.append(SkillGap(skill=s, required=True, user_has=True, note="已覆盖"))
        return gaps

    def _compute_score(self, jd_skills: set[str], resume_skills: set[str],
                       gaps: list[SkillGap]) -> int:
        if not jd_skills:
            return 50
        covered = sum(1 for g in gaps if g.user_has)
        total = len(gaps) if gaps else len(jd_skills)
        return min(98, max(10, int((covered / total) * 80) + 10))

    def _suggestions(self, missing: list[str], resume_text: str) -> list[SuggestionItem]:
        suggestions: list[SuggestionItem] = []
        if missing:
            suggestions.append(SuggestionItem(
                category="keyword",
                original="",
                suggestion=f"JD 要求但简历未体现的技能：{', '.join(missing[:8])}。仅当真实掌握时补充。",
                confidence="high",
            ))
        if re.search(r"负责|参与", resume_text):
            suggestions.append(SuggestionItem(
                category="wording",
                original="负责/参与",
                suggestion="将'负责''参与'改为'主导''设计并实现'等更强动词（仅当符合实际角色）",
                confidence="medium",
            ))
        if not re.search(r"\d+%|\d+倍|\d+万|\d+千|\d+亿", resume_text):
            suggestions.append(SuggestionItem(
                category="structure",
                original="",
                suggestion="简历中缺少量化成果，建议补充用户量、QPS、性能提升百分比等真实数据。",
                confidence="high",
            ))
        return suggestions

    def _run_integrity_checks(self, resume_text: str) -> list[IntegrityCheckItem]:
        checks: list[IntegrityCheckItem] = []
        resume_lower = resume_text.lower()

        if resume_lower.count("精通") > 3:
            checks.append(IntegrityCheckItem(
                severity="warning", category="exaggeration",
                description="'精通'出现次数较多，建议仅对真正深入掌握的技术使用",
                detail="可改为'熟练''掌握''具备X年经验'等更诚实的表达",
            ))

        for phrase in ["从0到1", "从零搭建", "独立负责所有", "全栈负责"]:
            if phrase in resume_lower:
                checks.append(IntegrityCheckItem(
                    severity="warning", category="scope",
                    description=f"检测到表述'{phrase}'，请确认实际职责范围是否匹配",
                    detail="可补充团队规模和协作说明，让面试官更准确评估",
                ))
                break

        if not checks:
            checks.append(IntegrityCheckItem(
                severity="pass", category="overall",
                description="完整性检查通过，未发现明显夸大风险",
                detail="建议在面试前再次确认所有数据准确",
            ))
        return checks

    @staticmethod
    def list_reports(db: Session, user_id: int) -> list[AnalysisReport]:
        return (
            db.query(AnalysisReport)
            .filter(AnalysisReport.user_id == user_id)
            .order_by(AnalysisReport.created_at.desc())
            .limit(20).all()
        )

    @staticmethod
    def get_report(db: Session, report_id: int, user_id: int) -> AnalysisReport | None:
        return (
            db.query(AnalysisReport)
            .filter(AnalysisReport.id == report_id, AnalysisReport.user_id == user_id)
            .first()
        )
