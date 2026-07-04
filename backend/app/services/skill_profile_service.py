from collections import Counter

from sqlalchemy.orm import Session

from app.models.models import Application, InterviewReview, WrittenTestReview
from app.schemas.skill_profile import SkillProfileResponse


class SkillProfileService:
    @staticmethod
    def get_profile(db: Session, user_id: int) -> SkillProfileResponse:
        apps = db.query(Application).filter(Application.user_id == user_id).count()
        interviews = (
            db.query(InterviewReview)
            .filter(InterviewReview.user_id == user_id)
            .all()
        )
        written_tests = (
            db.query(WrittenTestReview)
            .filter(WrittenTestReview.user_id == user_id)
            .all()
        )

        interview_weak: list[str] = []
        for iw in interviews:
            if iw.weak_points:
                interview_weak.append(iw.weak_points)

        tag_counter: Counter = Counter()
        for wt in written_tests:
            if wt.knowledge_tags:
                for t in wt.knowledge_tags:
                    tag_counter[t] += 1
            if not wt.solved and wt.stuck_point:
                tag_counter[wt.stuck_point] += 1

        weak_tags = [t for t, _ in tag_counter.most_common(10)]

        recent_suggestions: list[str] = []
        if weak_tags:
            recent_suggestions.append(f"笔试薄弱知识点：{', '.join(weak_tags[:5])}")
        if interview_weak:
            recent_suggestions.append(f"最近面试薄弱点：{interview_weak[-1][:80]}")

        return SkillProfileResponse(
            total_applications=apps,
            total_interviews=len(interviews),
            total_written_tests=len(written_tests),
            weak_skill_areas=weak_tags[:5],
            interview_weak_points_summary=interview_weak[-5:],
            written_test_weak_tags=weak_tags,
            recent_suggestions=recent_suggestions,
        )
