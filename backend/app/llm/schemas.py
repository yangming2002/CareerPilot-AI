from pydantic import BaseModel, Field


# --- Structured Resume Fields ---

class ParsedResumeFields(BaseModel):
    """LLM-extracted structured resume fields."""
    name: str = ""
    email: str = ""
    phone: str = ""
    education: list[dict] = Field(default_factory=list)  # [{school, degree, major, year}]
    skills: list[str] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)   # [{name, role, description}] — description must include ALL details, highlights, and bullet points
    internships: list[dict] = Field(default_factory=list)  # [{company, role, duration, description}]
    campus_experience: list[dict] = Field(default_factory=list)  # [{org, role, description}]
    self_evaluation: str = ""
    raw_summary: str = ""


# --- JD Match structured outputs ---

class ParsedJD(BaseModel):
    """Structured JD extraction."""
    company: str = ""
    position: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_years: int | None = None
    education: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    summary: str = ""


class LLMSkillGap(BaseModel):
    skill: str
    required: bool = True
    user_has: bool = False
    depth_match: str = ""  # "strong" / "partial" / "missing"
    note: str = ""


class LLMSuggestion(BaseModel):
    category: str  # "wording" / "structure" / "keyword" / "project" / "experience"
    original: str = ""
    suggestion: str
    confidence: str = "medium"  # "high" / "medium" / "low"
    grounded_in: str = ""  # which part of the resume supports this


class LLMIntegrityCheck(BaseModel):
    severity: str  # "pass" / "warning" / "risk"
    category: str
    description: str
    detail: str = ""
    fabricated_claim: str = ""
    resume_evidence: str = ""


class LLMMatchResult(BaseModel):
    """Complete JD match result from LLM (analysis only, no rewriting)."""
    match_score: int = Field(ge=0, le=100)
    jd_summary: str = ""
    resume_summary: str = ""
    skill_gaps: list[LLMSkillGap] = Field(default_factory=list)
    suggestions: list[LLMSuggestion] = Field(default_factory=list)
    integrity_checks: list[LLMIntegrityCheck] = Field(default_factory=list)


class LLMRevisedResume(BaseModel):
    """Standalone revised resume output."""
    revised_resume: str = ""


# --- Interview Coaching structured outputs ---

class CoachingResult(BaseModel):
    """Structured coaching output."""
    weak_point_summary: str = ""
    star_answer: str = ""
    simulated_followup: str = ""
    coaching_suggestions: list[str] = Field(default_factory=list)
    next_round_prep: list[str] = Field(default_factory=list)
