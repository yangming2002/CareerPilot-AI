from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analysis import JDMatchRequest, JDMatchResponse, ReportListItem
from app.services.analysis_service import AnalysisService

router = APIRouter()


@router.post("/analysis/jd-match", response_model=JDMatchResponse)
def jd_match(body: JDMatchRequest, db: Session = Depends(get_db)):
    return AnalysisService().analyze(db, body.resume_text, body.jd_text)


@router.get("/analysis/reports", response_model=list[ReportListItem])
def list_reports(db: Session = Depends(get_db)):
    return AnalysisService.list_reports(db)


@router.get("/analysis/reports/{report_id}", response_model=JDMatchResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = AnalysisService.get_report(db, report_id)
    if not report:
        from fastapi import HTTPException
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
