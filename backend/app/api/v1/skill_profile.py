from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.skill_profile import SkillProfileResponse
from app.services.skill_profile_service import SkillProfileService

router = APIRouter()


@router.get("/skill-profile", response_model=SkillProfileResponse)
def get_skill_profile(db: Session = Depends(get_db)):
    return SkillProfileService.get_profile(db)
