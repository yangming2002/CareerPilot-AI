from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class GuardFinding:
    severity: str  # "pass" | "warning" | "risk"
    category: str
    description: str
    detail: str = ""
    index: int | None = None  # which suggestion this relates to (0-based)


@dataclass
class GuardResult:
    guard_name: str
    passed: bool  # True if no risk-level findings
    findings: list[GuardFinding] = field(default_factory=list)
    revision_hints: list[str] = field(default_factory=list)

    @property
    def risk_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "risk")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning")


class GuardBase(ABC):
    name: str = "base"

    @abstractmethod
    def check(self, resume_text: str, suggestions: list[dict]) -> GuardResult:
        """Run the guard check and return findings."""
        ...
