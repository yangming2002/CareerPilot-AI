import datetime

from pydantic import BaseModel, Field


class WrittenTestCreate(BaseModel):
    company: str = Field(..., max_length=200)
    position: str | None = None
    test_date: str | None = None
    problem_type: str | None = None
    difficulty: str | None = None
    solved: bool = False
    stuck_point: str | None = None
    knowledge_tags: list[str] | None = None


class WrittenTestResponse(BaseModel):
    id: int
    company: str
    position: str | None = None
    test_date: str | None = None
    problem_type: str | None = None
    difficulty: str | None = None
    solved: bool
    stuck_point: str | None = None
    knowledge_tags: list[str] | None = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
