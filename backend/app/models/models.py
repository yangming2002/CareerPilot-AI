import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str] = mapped_column(String(200), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(100), default=None)
    application_date: Mapped[str | None] = mapped_column(String(20), default=None)
    resume_version: Mapped[str | None] = mapped_column(String(100), default=None)
    status: Mapped[str] = mapped_column(String(50), default="待投递")
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    status_history: Mapped[list["ApplicationStatusHistory"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("applications.id"), nullable=False
    )
    old_status: Mapped[str | None] = mapped_column(String(50), default=None)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    application: Mapped["Application"] = relationship(back_populates="status_history")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    jd_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    match_score: Mapped[int] = mapped_column(Integer, default=0)
    skill_gaps: Mapped[dict | None] = mapped_column(JSON, default=None)
    keyword_coverage: Mapped[dict | None] = mapped_column(JSON, default=None)
    suggestions: Mapped[list | None] = mapped_column(JSON, default=None)
    integrity_checks: Mapped[list | None] = mapped_column(JSON, default=None)
    raw_jd_summary: Mapped[str | None] = mapped_column(Text, default=None)
    raw_resume_summary: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class InterviewReview(Base):
    __tablename__ = "interview_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str | None] = mapped_column(String(200), default=None)
    round: Mapped[str] = mapped_column(String(50), nullable=False)
    interview_date: Mapped[str | None] = mapped_column(String(20), default=None)
    questions: Mapped[list | None] = mapped_column(JSON, default=None)
    weak_points: Mapped[str | None] = mapped_column(Text, default=None)
    coaching_suggestions: Mapped[list | None] = mapped_column(JSON, default=None)
    result: Mapped[str | None] = mapped_column(String(50), default=None)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class WrittenTestReview(Base):
    __tablename__ = "written_test_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str | None] = mapped_column(String(200), default=None)
    test_date: Mapped[str | None] = mapped_column(String(20), default=None)
    problem_type: Mapped[str | None] = mapped_column(String(100), default=None)
    difficulty: Mapped[str | None] = mapped_column(String(20), default=None)
    solved: Mapped[bool] = mapped_column(default=False)
    stuck_point: Mapped[str | None] = mapped_column(Text, default=None)
    knowledge_tags: Mapped[list | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
