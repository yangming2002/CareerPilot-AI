import datetime

from pydantic import BaseModel, Field


class InterviewCreate(BaseModel):
    company: str = Field(..., max_length=200)
    position: str | None = None
    round: str = Field(..., max_length=50)
    interview_date: str | None = None
    questions: list[dict] | None = None
    weak_points: str | None = None
    result: str | None = None


class InterviewResponse(BaseModel):
    id: int
    company: str
    position: str | None = None
    round: str
    interview_date: str | None = None
    questions: list[dict] | None = None
    weak_points: str | None = None
    coaching_suggestions: list[str] | None = None
    result: str | None = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
