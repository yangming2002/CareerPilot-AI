from typing import TypedDict

from app.llm.schemas import LLMMatchResult, ParsedResumeFields, ParsedJD


class CareerPilotState(TypedDict, total=False):
    # Input
    resume_text: str
    jd_text: str
    user_id: int
    session_id: str

    # Parsed
    parsed_jd: ParsedJD | None
    parsed_resume: ParsedResumeFields | None

    # Match
    rule_match_score: int
    llm_match_result: LLMMatchResult | None

    # Guard
    guard_passed: bool
    guard_findings: list[dict]
    guard_retry_count: int
    max_guard_retries: int

    # Output
    final_report_id: int | None
    degraded: bool
    degraded_reason: str
    progress_log: list[str]
    error: str | None
