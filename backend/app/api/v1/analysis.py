import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.analysis import JDMatchRequest, JDMatchResponse, ReportListItem
from app.services.analysis_service import AnalysisService
from app.services.llm_analysis_service import LLMAnalysisService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analysis/jd-match", response_model=JDMatchResponse)
def jd_match(
    body: JDMatchRequest,
    engine: str = Query("rule", description="Analysis engine: 'rule' or 'llm'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if engine == "llm":
        try:
            return LLMAnalysisService().analyze(db, body.resume_text, body.jd_text, current_user.id)
        except Exception as e:
            logger.exception("LLM analysis failed")
            raise HTTPException(
                status_code=502,
                detail=f"LLM analysis failed: {e}. Set engine=rule to use the rule-based engine.",
            )
    return AnalysisService().analyze(db, body.resume_text, body.jd_text, current_user.id)


@router.get("/analysis/reports", response_model=list[ReportListItem])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AnalysisService.list_reports(db, current_user.id)


@router.get("/analysis/reports/{report_id}", response_model=JDMatchResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = AnalysisService.get_report(db, report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return JDMatchResponse(
        id=report.id,
        match_score=report.match_score,
        skill_gaps=report.skill_gaps or [],
        keyword_coverage=report.keyword_coverage or [],
        suggestions=report.suggestions or [],
        integrity_checks=report.integrity_checks or [],
        jd_summary=report.raw_jd_summary or "",
        resume_summary=report.raw_resume_summary or "",
    )
