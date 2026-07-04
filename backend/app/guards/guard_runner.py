import logging
from dataclasses import dataclass, field

from app.guards.base import GuardBase, GuardResult
from app.guards.integrity_guard import IntegrityGuard
from app.guards.grounding_guard import GroundingGuard
from app.guards.prompt_injection_guard import PromptInjectionGuard

logger = logging.getLogger(__name__)


@dataclass
class RunnerResult:
    passed: bool
    results: list[GuardResult] = field(default_factory=list)
    combined_hints: list[str] = field(default_factory=list)

    @property
    def all_findings(self) -> list:
        out = []
        for r in self.results:
            out.extend(r.findings)
        return out


class GuardRunner:
    """Orchestrates multiple guards in sequence."""

    def __init__(self, guards: list[GuardBase] | None = None):
        self.guards = guards or [
            IntegrityGuard(),
            GroundingGuard(),
        ]

    def run(self, resume_text: str, suggestions: list[dict]) -> RunnerResult:
        results: list[GuardResult] = []
        all_passed = True

        for guard in self.guards:
            logger.debug(f"Running guard: {guard.name}")
            result = guard.check(resume_text, suggestions)
            results.append(result)
            if not result.passed:
                all_passed = False
                logger.warning(
                    f"Guard '{guard.name}' failed: {result.risk_count} risks, "
                    f"{result.warning_count} warnings"
                )

        combined_hints: list[str] = []
        for r in results:
            combined_hints.extend(r.revision_hints)

        return RunnerResult(
            passed=all_passed,
            results=results,
            combined_hints=combined_hints,
        )

    def check_input(self, text: str, text_type: str = "text") -> GuardResult:
        """Quick injection scan on raw user input."""
        guard = PromptInjectionGuard()
        return guard.check(text)
