from sqlalchemy.orm import Session

from app.models.models import InterviewReview
from app.schemas.interview import InterviewCreate


class InterviewService:
    @staticmethod
    def create(db: Session, data: InterviewCreate, user_id: int) -> InterviewReview:
        coaching = InterviewService._generate_coaching(data)
        review = InterviewReview(
            user_id=user_id,
            company=data.company,
            position=data.position,
            round=data.round,
            interview_date=data.interview_date,
            questions=data.questions,
            weak_points=data.weak_points,
            coaching_suggestions=coaching,
            result=data.result,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def list_all(db: Session, user_id: int) -> list[InterviewReview]:
        return (
            db.query(InterviewReview)
            .filter(InterviewReview.user_id == user_id)
            .order_by(InterviewReview.created_at.desc())
            .all()
        )

    @staticmethod
    def _generate_coaching(data: InterviewCreate) -> list[str]:
        tips: list[str] = []
        if data.weak_points:
            tips.append(f"针对薄弱点'{data.weak_points}'，建议准备 STAR 案例并模拟回答")
        if data.questions:
            tips.append(f"已记录 {len(data.questions)} 个面试问题，建议定期回顾并强化弱项")
        tips.append("下次面试前，针对本轮的薄弱环节做专项准备")
        if data.result and data.result in ("未通过", "已挂"):
            tips.append("本次未通过，建议分析失败原因并补充相关技能后再战")
        return tips
