import re

from app.guards.base import GuardBase, GuardFinding, GuardResult


class IntegrityGuard(GuardBase):
    """Check LLM suggestions for fabrication, exaggeration, and unsupported claims."""

    name = "integrity"

    # Patterns that indicate fabrication risk
    METRIC_PATTERN = re.compile(r"\d+%|\d+倍|\d+万|\d+千|\d+亿|\d+\s*(用户|DAU|MAU|QPS|PV|UV)")
    OVERSTATE_WORDS = {"精通", "专家", "资深", "从0到1", "从零搭建", "独立负责所有", "全栈负责"}
    TITLE_UPGRADES = {"负责": "主导", "参与": "主导", "协助": "独立完成", "开发": "架构设计"}

    def check(self, resume_text: str, suggestions: list[dict]) -> GuardResult:
        findings: list[GuardFinding] = []
        resume_lower = resume_text.lower()

        for i, s in enumerate(suggestions):
            suggestion_text = s.get("suggestion", "")
            grounded_in = s.get("grounded_in", "")
            original = s.get("original", "")

            # 1. Check for fabricated metrics not in resume
            metrics_in_suggestion = self.METRIC_PATTERN.findall(suggestion_text)
            if metrics_in_suggestion:
                metrics_in_resume = self.METRIC_PATTERN.findall(resume_text)
                new_metrics = [m for m in metrics_in_suggestion if m not in metrics_in_resume]
                if new_metrics:
                    findings.append(GuardFinding(
                        severity="risk",
                        category="fabrication",
                        description=f"建议引入了简历中不存在的量化数据：{', '.join(new_metrics[:3])}",
                        detail=f"简历中未找到这些指标，请勿编造数字。可改为'用真实数据量化成果'的提示。",
                        index=i,
                    ))

            # 2. Check for overstated words not supported by resume
            for word in self.OVERSTATE_WORDS:
                if word in suggestion_text and word not in resume_text:
                    findings.append(GuardFinding(
                        severity="warning",
                        category="exaggeration",
                        description=f"建议使用了'{word}'，但简历中未找到对应依据",
                        detail="建议改为更诚实的表达，如'参与''协作搭建'等。",
                        index=i,
                    ))
                    break  # one warning per suggestion

            # 3. Check grounded_in actually references resume content
            if grounded_in and grounded_in not in resume_text:
                findings.append(GuardFinding(
                    severity="warning",
                    category="grounding",
                    description=f"建议声称依据'{grounded_in[:60]}'，但简历中找不到该片段",
                    detail="请确保每一条建议都在简历原文中有确切出处。",
                    index=i,
                ))

            # 4. Check title inflation
            for weak, strong in self.TITLE_UPGRADES.items():
                if weak in original and strong in suggestion_text and weak not in resume_lower:
                    findings.append(GuardFinding(
                        severity="warning",
                        category="exaggeration",
                        description=f"建议将'{weak}'改为'{strong}'，但简历中无领导角色证据",
                        detail="请确认实际职责后再调整动词。",
                        index=i,
                    ))

        passed = not any(f.severity == "risk" for f in findings)

        hints: list[str] = []
        if not passed:
            hints.append("请移除简历中不存在的数据和指标，只基于真实经历给出建议。")
            hints.append("如简历信息不足，建议用户补充真实数据而非生成虚假数字。")

        return GuardResult(
            guard_name=self.name,
            passed=passed,
            findings=findings,
            revision_hints=hints,
        )
