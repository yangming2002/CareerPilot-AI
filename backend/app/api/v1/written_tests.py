from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.written_test import WrittenTestCreate, WrittenTestResponse
from app.services.written_test_service import WrittenTestService

router = APIRouter()


@router.post("/written-tests/reviews", response_model=WrittenTestResponse, status_code=201)
def create_written_test_review(body: WrittenTestCreate, db: Session = Depends(get_db)):
    return WrittenTestService.create(db, body)


@router.get("/written-tests/reviews", response_model=list[WrittenTestResponse])
def list_written_test_reviews(db: Session = Depends(get_db)):
    return WrittenTestService.list_all(db)
