from dataclasses import dataclass, field

from app.guards.base import GuardBase, GuardResult
from app.guards.integrity_guard import IntegrityGuard
from app.guards.grounding_guard import GroundingGuard
from app.guards.prompt_injection_guard import PromptInjectionGuard

from loguru import logger


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
    """Orchestrates multiple guards in sequence.

    Blocking guards (IntegrityGuard): trigger LLM retry on failure.
    Advisory guards (GroundingGuard): run and report but never block.
    """

    BLOCKING_GUARDS: list[type[GuardBase]] = [IntegrityGuard]
    ADVISORY_GUARDS: list[type[GuardBase]] = [GroundingGuard]

    def __init__(self, blocking: list[GuardBase] | None = None,
                 advisory: list[GuardBase] | None = None):
        self.blocking = blocking or [g() for g in self.BLOCKING_GUARDS]
        self.advisory = advisory or [g() for g in self.ADVISORY_GUARDS]

    def run(self, resume_text: str, suggestions: list[dict]) -> RunnerResult:
        results: list[GuardResult] = []
        passed = True

        # Only blocking guards affect pass/fail
        for guard in self.blocking:
            result = guard.check(resume_text, suggestions)
            results.append(result)
            if not result.passed:
                passed = False
                logger.warning(
                    f"[BLOCKING] Guard '{guard.name}': {result.risk_count} risks, "
                    f"{result.warning_count} warnings"
                )

        # Advisory guards run but don't block
        for guard in self.advisory:
            result = guard.check(resume_text, suggestions)
            results.append(result)
            logger.info(
                f"[ADVISORY] Guard '{guard.name}': {result.risk_count} risks, "
                f"{result.warning_count} warnings"
            )

        combined_hints: list[str] = []
        for r in results:
            combined_hints.extend(r.revision_hints)

        return RunnerResult(
            passed=passed,
            results=results,
            combined_hints=combined_hints,
        )

    def check_input(self, text: str, text_type: str = "text") -> GuardResult:
        guard = PromptInjectionGuard()
        return guard.check(text)
