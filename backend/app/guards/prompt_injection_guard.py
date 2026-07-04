import re

from app.guards.base import GuardBase, GuardFinding, GuardResult


class PromptInjectionGuard(GuardBase):
    """Detect prompt injection attempts in user-provided JD and resume text."""

    name = "prompt_injection"

    # High-confidence injection patterns
    OVERRIDE_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above|system)\s+(instructions?|rules?|prompts?)", re.I),
        re.compile(r"forget\s+(your|all)\s+(guidelines?|instructions?|rules?)", re.I),
        re.compile(r"you\s+are\s+(now|no\s+longer)\s+a\b", re.I),
        re.compile(r"output\s+(your\s+)?system\s+(prompt|message|instruction)", re.I),
        re.compile(r"print\s+(your\s+)?(system\s+)?(prompt|instructions?)", re.I),
        re.compile(r"\[system\]|\[/system\]|\[prompt\]|\[/prompt\]", re.I),
        re.compile(r"<\|.*\|>|\[INST\]|\[/INST\]", re.I),
    ]

    # Suspicious but lower confidence
    SUSPICIOUS_PATTERNS = [
        re.compile(r"ignore\s+the\s+(above|following)", re.I),
        re.compile(r"do\s+not\s+(follow|obey|listen\s+to)", re.I),
        re.compile(r"your\s+(real|true|actual)\s+(role|purpose|job)\s+is", re.I),
        re.compile(r"pretend\s+(you\s+are|to\s+be)", re.I),
        re.compile(r"act\s+as\s+(if|though)\s+you\s+are", re.I),
    ]

    def check(self, resume_text: str, suggestions: list[dict] | None = None) -> GuardResult:
        """Check a text for prompt injection. suggestions parameter ignored for this guard."""
        findings: list[GuardFinding] = []

        # Check in resume_text (which for injection check we pass as the text to scan)
        text = resume_text

        for pattern in self.OVERRIDE_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(GuardFinding(
                    severity="risk",
                    category="prompt_injection",
                    description=f"检测到疑似指令注入：'{match.group().strip()}'",
                    detail="用户输入包含试图覆盖系统指令的内容，已拦截。",
                ))
                return GuardResult(
                    guard_name=self.name,
                    passed=False,
                    findings=findings,
                    revision_hints=["请移除试图覆盖系统行为的指令内容。"],
                )

        for pattern in self.SUSPICIOUS_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(GuardFinding(
                    severity="warning",
                    category="suspicious_input",
                    description=f"检测到可疑指令：'{match.group().strip()}'",
                    detail="该内容可能是合法文本，但包含类似指令注入的语言。",
                ))

        return GuardResult(
            guard_name=self.name,
            passed=not any(f.severity == "risk" for f in findings),
            findings=findings,
        )
