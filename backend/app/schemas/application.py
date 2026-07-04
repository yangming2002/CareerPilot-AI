import datetime

from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    company: str = Field(..., max_length=200)
    position: str = Field(..., max_length=200)
    channel: str | None = None
    application_date: str | None = None
    resume_version: str | None = None
    status: str = "待投递"
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    company: str | None = None
    position: str | None = None
    channel: str | None = None
    application_date: str | None = None
    resume_version: str | None = None
    notes: str | None = None


class StatusUpdate(BaseModel):
    status: str


class StatusHistoryItem(BaseModel):
    id: int
    old_status: str | None
    new_status: str
    changed_at: datetime.datetime

    class Config:
        from_attributes = True


class ApplicationResponse(BaseModel):
    id: int
    company: str
    position: str
    channel: str | None = None
    application_date: str | None = None
    resume_version: str | None = None
    status: str
    notes: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None
    status_history: list[StatusHistoryItem] = []

    class Config:
        from_attributes = True


class CooldownInfo(BaseModel):
    company: str
    has_active_application: bool
    last_application_date: str | None = None
    last_status: str | None = None
    in_cooldown: bool = False
    cooldown_message: str = ""
