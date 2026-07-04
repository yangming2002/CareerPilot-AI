from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.interview import InterviewCreate, InterviewResponse
from app.services.interview_service import InterviewService

router = APIRouter()


@router.post("/interviews/reviews", response_model=InterviewResponse, status_code=201)
def create_interview_review(
    body: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return InterviewService.create(db, body, current_user.id)


@router.get("/interviews/reviews", response_model=list[InterviewResponse])
def list_interview_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return InterviewService.list_all(db, current_user.id)
