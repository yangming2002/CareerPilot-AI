from pydantic import BaseModel, Field


class JDMatchRequest(BaseModel):
    resume_text: str = Field(..., min_length=1, description="用户简历全文")
    jd_text: str = Field(..., min_length=1, description="目标岗位 JD 全文")


class SuggestionItem(BaseModel):
    category: str  # e.g. "wording", "structure", "keyword", "project"
    original: str
    suggestion: str
    confidence: str  # "high" | "medium" | "low"


class IntegrityCheckItem(BaseModel):
    severity: str  # "pass" | "warning" | "risk"
    category: str
    description: str
    detail: str = ""


class SkillGap(BaseModel):
    skill: str
    required: bool = True
    user_has: bool = False
    note: str = ""


class KeywordCoverage(BaseModel):
    keyword: str
    in_resume: bool
    in_jd: bool


class JDMatchResponse(BaseModel):
    id: int | None = None
    match_score: int
    skill_gaps: list[SkillGap] = []
    keyword_coverage: list[KeywordCoverage] = []
    suggestions: list[SuggestionItem] = []
    integrity_checks: list[IntegrityCheckItem] = []
    jd_summary: str = ""
    resume_summary: str = ""
    degraded: bool = False
    degraded_reason: str = ""
    progress_log: list[str] = []
    revised_resume: str = ""


class ReportListItem(BaseModel):
    id: int
    match_score: int
    created_at: str

    class Config:
        from_attributes = True
