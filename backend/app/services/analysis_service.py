import hashlib
import re

from sqlalchemy.orm import Session

from app.models.models import AnalysisReport
from app.schemas.analysis import (
    IntegrityCheckItem,
    JDMatchResponse,
    KeywordCoverage,
    SkillGap,
    SuggestionItem,
)


class AnalysisService:
    """JD-Resume matching using rule-based heuristics (MVP)."""

    TECH_SKILLS = {
        "python", "java", "javascript", "typescript", "go", "rust", "c++", "c#",
        "sql", "react", "vue", "angular", "node.js", "django", "flask", "fastapi",
        "spring", "docker", "kubernetes", "aws", "azure", "gcp", "redis",
        "postgresql", "mysql", "mongodb", "elasticsearch", "kafka", "rabbitmq",
        "tensorflow", "pytorch", "pandas", "numpy", "spark", "hadoop",
        "git", "ci/cd", "jenkins", "terraform", "ansible", "linux",
        "machine learning", "deep learning", "nlp", "computer vision",
        "llm", "langchain", "agent", "rag", "prompt engineering",
    }

    SOFT_SKILLS = {
        "communication", "teamwork", "leadership", "problem solving",
        "critical thinking", "agile", "scrum", "project management",
        "stakeholder management", "cross-functional",
    }

    def analyze(self, db: Session, resume_text: str, jd_text: str, user_id: int) -> JDMatchResponse:
        resume_lower = resume_text.lower()
        jd_lower = jd_text.lower()

        jd_skills = self._extract_skills(jd_lower)
        resume_skills = self._extract_skills(resume_lower)

        skill_gaps = self._compute_skill_gaps(jd_skills, resume_skills)
        keyword_coverage = self._compute_keyword_coverage(jd_text, resume_text)
        suggestions = self._generate_suggestions(jd_skills, resume_skills, resume_text)
        integrity_checks = self._run_integrity_checks(resume_text)
        match_score = self._compute_score(jd_skills, resume_skills, skill_gaps)

        jd_summary = self._summarize(jd_text, max_len=120)
        resume_summary = self._summarize(resume_text, max_len=120)

        resume_hash = hashlib.sha256(resume_text.encode()).hexdigest()
        jd_hash = hashlib.sha256(jd_text.encode()).hexdigest()

        report = AnalysisReport(
            user_id=user_id,
            resume_text_hash=resume_hash,
            jd_text_hash=jd_hash,
            match_score=match_score,
            skill_gaps=[g.model_dump() for g in skill_gaps],
            keyword_coverage=[k.model_dump() for k in keyword_coverage],
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
            keyword_coverage=keyword_coverage,
            suggestions=suggestions,
            integrity_checks=integrity_checks,
            jd_summary=jd_summary,
            resume_summary=resume_summary,
        )

    # ---------- private helpers ----------

    def _extract_skills(self, text: str) -> set[str]:
        found: set[str] = set()
        for skill in self.TECH_SKILLS | self.SOFT_SKILLS:
            if skill in text:
                found.add(skill)
        return found

    def _compute_skill_gaps(self, jd_skills: set[str], resume_skills: set[str]) -> list[SkillGap]:
        gaps: list[SkillGap] = []
        for s in sorted(jd_skills - resume_skills):
            gaps.append(SkillGap(skill=s, required=True, user_has=False, note="JD 要求但简历未明确提及"))
        for s in sorted(jd_skills & resume_skills):
            gaps.append(SkillGap(skill=s, required=True, user_has=True, note="已覆盖"))
        return gaps

    def _compute_keyword_coverage(self, jd_text: str, resume_text: str) -> list[KeywordCoverage]:
        keywords = re.findall(r"[一-鿿\w]+", jd_text.lower())
        seen: set[str] = set()
        result: list[KeywordCoverage] = []
        for kw in keywords[:30]:
            if kw in seen or len(kw) < 3:
                continue
            seen.add(kw)
            result.append(KeywordCoverage(
                keyword=kw,
                in_jd=True,
                in_resume=kw.lower() in resume_text.lower(),
            ))
        return result

    def _generate_suggestions(
        self, jd_skills: set[str], resume_skills: set[str], resume_text: str
    ) -> list[SuggestionItem]:
        suggestions: list[SuggestionItem] = []
        missing = jd_skills - resume_skills
        if missing:
            suggestions.append(SuggestionItem(
                category="keyword",
                original="",
                suggestion=f"考虑在简历中补充相关技能关键词：{', '.join(sorted(missing)[:8])}（仅当真实掌握时）",
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
                suggestion="简历中缺少量化成果。在真实数据基础上，补充用户量、性能提升百分比、收入影响等量化指标",
                confidence="high",
            ))
        else:
            suggestions.append(SuggestionItem(
                category="structure",
                original="",
                suggestion="已检测到量化指标，请确认所有数字均为真实数据，避免估算或夸大",
                confidence="medium",
            ))

        return suggestions

    def _run_integrity_checks(self, resume_text: str) -> list[IntegrityCheckItem]:
        checks: list[IntegrityCheckItem] = []
        resume_lower = resume_text.lower()

        if re.search(r"精通.*\n.*\n.*\n", resume_text) or resume_lower.count("精通") > 3:
            checks.append(IntegrityCheckItem(
                severity="warning",
                category="exaggeration",
                description="简历中'精通'出现次数较多，建议仅对真正深入掌握的技术使用",
                detail="可改为'熟练''掌握''具备X年经验'等更诚实的表达",
            ))

        overpromise = ["从0到1", "从零搭建", "独立负责所有", "全栈负责"]
        for phrase in overpromise:
            if phrase in resume_lower or phrase in resume_text:
                checks.append(IntegrityCheckItem(
                    severity="warning",
                    category="scope",
                    description=f"检测到表述'{phrase}'，请确认实际职责范围是否匹配",
                    detail="可补充团队规模和协作说明，让面试官更准确评估",
                ))
                break

        if not checks:
            checks.append(IntegrityCheckItem(
                severity="pass",
                category="overall",
                description="初步完整性检查通过，未发现明显夸大风险",
                detail="建议在面试前再次确认所有数据准确",
            ))

        return checks

    def _compute_score(
        self, jd_skills: set[str], resume_skills: set[str], gaps: list[SkillGap]
    ) -> int:
        if not jd_skills:
            return 50
        covered = sum(1 for g in gaps if g.user_has)
        total = len(gaps) if gaps else len(jd_skills)
        base = int((covered / total) * 80) if total > 0 else 40
        return min(98, max(10, base + 10))

    def _summarize(self, text: str, max_len: int = 120) -> str:
        return text[:max_len] + ("…" if len(text) > max_len else "")

    # ---------- list / detail ----------

    @staticmethod
    def list_reports(db: Session, user_id: int) -> list[AnalysisReport]:
        return (
            db.query(AnalysisReport)
            .filter(AnalysisReport.user_id == user_id)
            .order_by(AnalysisReport.created_at.desc())
            .limit(20)
            .all()
        )

    @staticmethod
    def get_report(db: Session, report_id: int, user_id: int) -> AnalysisReport | None:
        return (
            db.query(AnalysisReport)
            .filter(AnalysisReport.id == report_id, AnalysisReport.user_id == user_id)
            .first()
        )
