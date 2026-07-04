from pydantic import BaseModel


class SkillProfileResponse(BaseModel):
    total_applications: int = 0
    total_interviews: int = 0
    total_written_tests: int = 0
    weak_skill_areas: list[str] = []
    interview_weak_points_summary: list[str] = []
    written_test_weak_tags: list[str] = []
    recent_suggestions: list[str] = []
