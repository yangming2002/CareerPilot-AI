"""Conversational Agent API."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.agent_chat.orchestrator import get_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = ""
    conversation_id: str = ""
    resume_text: str = ""
    jd_text: str = ""
    company: str = ""
    position: str = ""


@router.post("/agent/chat")
def agent_chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Talk to the CareerPilot conversational Agent."""
    agent = get_agent()
    return agent.chat(
        user_message=body.message,
        user_id=current_user.id,
        conversation_id=body.conversation_id,
        resume_text=body.resume_text,
        jd_text=body.jd_text,
        company=body.company,
        position=body.position,
    )
