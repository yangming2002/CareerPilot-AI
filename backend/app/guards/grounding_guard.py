import re

from app.guards.base import GuardBase, GuardFinding, GuardResult


class GroundingGuard(GuardBase):
    """Check whether each suggestion has supporting evidence in the resume."""

    name = "grounding"

    def check(self, resume_text: str, suggestions: list[dict]) -> GuardResult:
        findings: list[GuardFinding] = []

        for i, s in enumerate(suggestions):
            suggestion_text = s.get("suggestion", "")
            grounded_in = s.get("grounded_in", "")

            if not grounded_in:
                findings.append(GuardFinding(
                    severity="warning",
                    category="ungrounded",
                    description=f"第{i+1}条建议缺少简历依据（grounded_in 为空）",
                    detail="每条优化建议应标注在简历中的出处。",
                    index=i,
                ))
                continue

            # Check if grounded_in text actually appears in resume (fuzzy)
            if not self._fuzzy_match(grounded_in, resume_text):
                findings.append(GuardFinding(
                    severity="risk",
                    category="ungrounded",
                    description=f"第{i+1}条建议声称依据'{grounded_in[:80]}'，但简历中找不到匹配内容",
                    detail="请核实该建议是否有简历原文支撑，如没有请移除。",
                    index=i,
                ))
            else:
                findings.append(GuardFinding(
                    severity="pass",
                    category="grounded",
                    description=f"第{i+1}条建议有简历依据",
                    index=i,
                ))

        passed = not any(f.severity == "risk" for f in findings)

        hints: list[str] = []
        if not passed:
            hints.append("部分建议缺少简历原文依据，请仅基于简历中确实存在的内容给出建议。")

        return GuardResult(
            guard_name=self.name,
            passed=passed,
            findings=findings,
            revision_hints=hints,
        )

    @staticmethod
    def _fuzzy_match(needle: str, haystack: str) -> bool:
        """Check if at least 60% of the words in needle appear in haystack."""
        if len(needle) < 10:
            return needle.lower() in haystack.lower()
        words = re.findall(r"\w+", needle.lower())
        if not words:
            return False
        matched = sum(1 for w in words if w in haystack.lower())
        return (matched / len(words)) >= 0.5
