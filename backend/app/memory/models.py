"""Memory system models: user facts and JD archive."""
import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserFact(Base):
    """Extracted fact from a user's resume: a skill, project, experience, etc."""
    __tablename__ = "user_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # "skill", "project", "internship", "education", "achievement", "weakness"

    content: Mapped[str] = mapped_column(Text, nullable=False)
    # The actual fact text

    source: Mapped[str] = mapped_column(String(100), default="resume")
    # Where this fact came from: "resume_v1", "interview_review", "jd_match_report_42"

    confidence: Mapped[str] = mapped_column(String(20), default="auto")
    # "auto" (system extracted), "confirmed" (user approved), "manual" (user entered)

    tags: Mapped[str | None] = mapped_column(Text, default=None)
    # Comma-separated tags for retrieval: "LangGraph,Agent,FastAPI"

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class JDArchive(Base):
    """Stored JD analysis for future reference."""
    __tablename__ = "jd_archive"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    company: Mapped[str | None] = mapped_column(String(200), default=None)
    position: Mapped[str | None] = mapped_column(String(200), default=None)
    jd_text: Mapped[str] = mapped_column(Text, nullable=False)
    jd_summary: Mapped[str | None] = mapped_column(Text, default=None)

    required_skills: Mapped[str | None] = mapped_column(Text, default=None)
    # JSON array of required skill strings

    match_score: Mapped[int | None] = mapped_column(Integer, default=None)
    # The match score when this JD was analyzed

    salary_range: Mapped[str | None] = mapped_column(String(100), default=None)
    # Free text: "15k-25k", "面议", etc.

    status: Mapped[str] = mapped_column(String(20), default="active")
    # "active", "expired", "applied", "offer"

    tags: Mapped[str | None] = mapped_column(Text, default=None)
    # Extracted skill tags for search

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
