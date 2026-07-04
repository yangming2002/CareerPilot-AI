from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.interview import InterviewCreate, InterviewResponse
from app.services.interview_service import InterviewService

router = APIRouter()


@router.post("/interviews/reviews", response_model=InterviewResponse, status_code=201)
def create_interview_review(body: InterviewCreate, db: Session = Depends(get_db)):
    return InterviewService.create(db, body)


@router.get("/interviews/reviews", response_model=list[InterviewResponse])
def list_interview_reviews(db: Session = Depends(get_db)):
    return InterviewService.list_all(db)
