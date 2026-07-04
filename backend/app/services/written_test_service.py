from sqlalchemy.orm import Session

from app.models.models import WrittenTestReview
from app.schemas.written_test import WrittenTestCreate


class WrittenTestService:
    @staticmethod
    def create(db: Session, data: WrittenTestCreate) -> WrittenTestReview:
        review = WrittenTestReview(
            company=data.company,
            position=data.position,
            test_date=data.test_date,
            problem_type=data.problem_type,
            difficulty=data.difficulty,
            solved=data.solved,
            stuck_point=data.stuck_point,
            knowledge_tags=data.knowledge_tags,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def list_all(db: Session) -> list[WrittenTestReview]:
        return db.query(WrittenTestReview).order_by(WrittenTestReview.created_at.desc()).all()
