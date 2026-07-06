from fastapi import APIRouter

from app.api.v1.analysis import router as analysis_router
from app.api.v1.applications import router as app_router
from app.api.v1.auth import router as auth_router
from app.api.v1.interviews import router as interview_router
from app.api.v1.written_tests import router as written_test_router
from app.api.v1.knowledge import router as kb_router
from app.api.v1.skill_profile import router as skill_profile_router

router = APIRouter(prefix="/api/v1")
router.include_router(kb_router, tags=["knowledge"])
router.include_router(auth_router, tags=["auth"])
router.include_router(analysis_router, tags=["analysis"])
router.include_router(app_router, tags=["applications"])
router.include_router(interview_router, tags=["interviews"])
router.include_router(written_test_router, tags=["written-tests"])
router.include_router(skill_profile_router, tags=["skill-profile"])
