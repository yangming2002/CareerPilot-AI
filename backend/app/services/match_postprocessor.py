"""
Post-processing layer that corrects common LLM mistakes in match analysis.
Runs AFTER LLM output, BEFORE saving/returning to frontend.
Code-enforced rules that LLM prompts alone can't reliably guarantee.
"""
import re

from app.schemas.analysis import IntegrityCheckItem, JDMatchResponse, SkillGap, SuggestionItem


class MatchPostprocessor:
    """Apply deterministic corrections to LLM match output."""

    def process(self, response: JDMatchResponse, jd_text: str, resume_text: str) -> JDMatchResponse:
        self._fix_at_least_one_gaps(response, jd_text)
        self._remove_hallucinated_gaps(response, jd_text)
        self._fix_preferred_vs_required(response, jd_text)
        self._detect_github(response, resume_text)
        self._clean_revised_resume_placeholders(response, resume_text)
        return response

    # ── Rule 1: "至少一门 A/B/C" — if resume has one, mark all as covered ──

    AT_LEAST_ONE_PATTERNS = [
        re.compile(r"(?:熟悉|掌握|了解|精通).{0,20}(?:等|/).{0,30}(?:至少(?:一|1)[门种个])"),
        re.compile(r"(?:至少(?:一|1)[门种个]).{0,20}(?:熟悉|掌握|了解|精通)"),
    ]

    def _fix_at_least_one_gaps(self, response: JDMatchResponse, jd_text: str) -> None:
        """If JD says 'at least one of A/B/C' and resume covers one, unmark others."""
        for pattern in self.AT_LEAST_ONE_PATTERNS:
            match = pattern.search(jd_text)
            if not match:
                continue

            # Extract candidate skills from this JD phrase
            group_text = jd_text[match.start():match.end() + 60]
            # Simple extraction of capitalized/technical terms
            candidates = set(re.findall(r'[A-Za-z+#]{2,}', group_text))

            # Check if resume covers at least one
            covered_in_group = [
                g for g in response.skill_gaps
                if g.skill.strip() in candidates and g.user_has
            ]

            if covered_in_group:
                # Mark all candidates in this group as covered
                for g in response.skill_gaps:
                    if g.skill.strip() in candidates and not g.user_has:
                        g.user_has = True
                        g.required = False
                        g.note = f"JD 要求至少一门即可（简历已覆盖同组的 {covered_in_group[0].skill}），此项为可选加分项"
            break

    # ── Rule 2: Remove gaps for things JD never mentions ──

    def _remove_hallucinated_gaps(self, response: JDMatchResponse, jd_text: str) -> None:
        """If JD doesn't mention '缓存' at all, remove caching from gaps."""
        jd_lower = jd_text.lower()
        to_keep = []

        for g in response.skill_gaps:
            skill_lower = g.skill.lower().strip()
            # Check if skill appears in JD
            in_jd = skill_lower in jd_lower or any(
                word in jd_lower for word in skill_lower.split()
            )
            if in_jd or g.user_has:
                to_keep.append(g)
            else:
                # Add as integrity check instead of gap
                response.integrity_checks.append(
                    IntegrityCheckItem(
                        severity="pass",
                        category="system",
                        description=f"已移除误报缺口：'{g.skill}'（JD 未明确要求）",
                    )
                )

        # Only replace if we removed some
        if len(to_keep) < len(response.skill_gaps):
            response.skill_gaps = to_keep

    # ── Rule 3: Fix preferred vs required classification ──

    PREFERRED_MARKERS = ["优先", "加分", "优先考虑", "有.*经验者优先", "者优先"]

    def _fix_preferred_vs_required(self, response: JDMatchResponse, jd_text: str) -> None:
        """Skills near '优先' in JD should be marked preferred, not required."""
        for g in response.skill_gaps:
            skill = g.skill.strip()
            if not skill or g.user_has:
                continue

            # Check if this skill appears near a "优先" marker
            for marker in self.PREFERRED_MARKERS:
                pattern = re.compile(
                    f"{re.escape(skill)}.{{0,100}}{marker}|{marker}.{{0,100}}{re.escape(skill)}"
                )
                if pattern.search(jd_text):
                    g.required = False
                    g.note = g.note.replace("JD 要求", "JD 列为优先加分项")
                    if "但简历未" in g.note:
                        g.note = f"JD 列为加分项（非必须），当前简历未提及。{g.note.split('但')[0] if '但' in g.note else ''}"
                    break

    # ── Rule 4: Detect GitHub link → open source covered ──

    GITHUB_PATTERN = re.compile(r'github\.com/[\w.-]+', re.I)

    def _detect_github(self, response: JDMatchResponse, resume_text: str) -> None:
        """If resume has a GitHub link, mark 开源项目经验 as covered."""
        if self.GITHUB_PATTERN.search(resume_text):
            for g in response.skill_gaps:
                if "开源" in g.skill and not g.user_has:
                    g.user_has = True
                    g.note = "简历中含 GitHub 链接，视为有开源项目经验"
                    break

    # ── Rule 5: Remove 【待补充】placeholders for already-present info ──

    PLACEHOLDER_PATTERN = re.compile(r'【待补充[：:][^】]+】')

    def _clean_revised_resume_placeholders(
        self, response: JDMatchResponse, resume_text: str
    ) -> None:
        """Remove false placeholders: if education exists, remove education placeholders."""
        if not response.revised_resume:
            return

        revised = response.revised_resume
        resume_lower = resume_text.lower()

        # Key fields to check
        checks = [
            (["学历", "学校", "education", "入学年份", "毕业"], "教育信息"),
            (["GPA", "均分"], "GPA"),
            (["技能", "skill"], "技能"),
            (["项目", "project"], "项目经历"),
        ]

        placeholders = self.PLACEHOLDER_PATTERN.findall(revised)
        for ph in placeholders:
            ph_lower = ph.lower()
            for keywords, field_name in checks:
                if any(kw in ph_lower for kw in keywords):
                    # Check if this info exists in the resume
                    if any(kw in resume_lower for kw in keywords):
                        revised = revised.replace(ph, f"（{field_name}已填写，详见上方）")
                    break

        response.revised_resume = revised
