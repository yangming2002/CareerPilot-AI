import logging
import tempfile

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import InputInsufficientError, LLMConnectionError
from app.llm.client import get_llm_client
from app.llm.prompts import RESUME_PARSE_SYSTEM, RESUME_PARSE_USER
from app.llm.schemas import ParsedResumeFields
from app.models.user import User
from app.schemas.analysis import JDMatchRequest, JDMatchResponse, ReportListItem
from app.services.analysis_service import AnalysisService
from app.services.llm_analysis_service import LLMAnalysisService
from app.utils.file_parser import extract_text

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
        except InputInsufficientError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except LLMConnectionError:
            # Auto-degrade to rule engine
            result = AnalysisService().analyze(db, body.resume_text, body.jd_text, current_user.id)
            result.degraded = True
            result.degraded_reason = "LLM 服务暂时不可用，已自动切换为规则引擎分析"
            return result
        except Exception as e:
            logger.exception("LLM analysis failed unexpectedly")
            # Also degrade on unknown errors
            result = AnalysisService().analyze(db, body.resume_text, body.jd_text, current_user.id)
            result.degraded = True
            result.degraded_reason = f"LLM 分析异常（{e}），已自动切换为规则引擎分析"
            return result

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
        raise HTTPException(status_code=404, detail="分析报告不存在或无权访问")
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


@router.post("/analysis/parse-resume", response_model=ParsedResumeFields)
async def parse_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF/DOCX/TXT resume and get structured fields back."""
    ALLOWED = {".pdf", ".docx", ".doc", ".txt", ".md"}
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式 {ext}，请上传 PDF、DOCX 或 TXT 文件。")

    try:
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件过大，请上传小于 5MB 的简历文件。")

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        raw_text = extract_text(tmp_path, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=422, detail="文件解析失败，请确认文件未损坏，或尝试直接粘贴简历内容。")
    finally:
        import os
        if 'tmp_path' in locals():
            os.unlink(tmp_path)

    if len(raw_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="文件解析后内容过短，可能文件为空白或仅为图片。请尝试直接粘贴简历内容。")

    # Parse with LLM
    llm = get_llm_client()
    try:
        fields = llm.complete_structured(
            system=RESUME_PARSE_SYSTEM,
            user=RESUME_PARSE_USER.format(resume_text=raw_text[:6000]),
            output_schema=ParsedResumeFields,
        )
        if fields is None:
            raise Exception("LLM parsing returned None")
        return fields
    except Exception as e:
        logger.exception("Resume parsing failed")
        # Return raw text as fallback
        return ParsedResumeFields(raw_summary=raw_text[:500])


@router.get("/analysis/export-md/{report_id}")
def export_markdown(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the revised resume as a Markdown file."""
    from fastapi.responses import PlainTextResponse

    report = AnalysisService.get_report(db, report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="分析报告不存在或无权访问")

    suggestions_data = report.suggestions or []
    revised = ""
    for s in suggestions_data:
        if isinstance(s, dict) and s.get("suggestion"):
            revised += s["suggestion"] + "\n\n"

    if not revised.strip():
        revised = "暂无改写内容，请先运行 LLM 分析并生成改写后的简历。"

    headers = {"Content-Disposition": "attachment; filename=revised_resume.md"}
    return PlainTextResponse(content=revised, media_type="text/markdown", headers=headers)


@router.get("/analysis/export-pdf/{report_id}")
def export_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export revised resume as PDF."""
    import markdown as md_lib
    from weasyprint import HTML

    report = AnalysisService.get_report(db, report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="分析报告不存在或无权访问")

    suggestions_data = report.suggestions or []
    content_md = ""
    for s in suggestions_data:
        if isinstance(s, dict) and s.get("suggestion"):
            content_md += s["suggestion"] + "\n\n"

    if not content_md.strip():
        content_md = "暂无改写内容，请先运行 LLM 分析并生成改写后的简历。"

    html_body = md_lib.markdown(content_md, extensions=["extra", "nl2br"])
    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>改写后的简历</title>
<style>
body {{ font-family: "Microsoft YaHei", "SimHei", sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.8; color: #1f2937; }}
h1, h2, h3 {{ color: #111827; }} p {{ margin: 8px 0; }}
</style></head>
<body>{html_body}</body></html>"""

    pdf_bytes = HTML(string=html_doc).write_pdf()
    headers = {"Content-Disposition": "attachment; filename=revised_resume.pdf"}
    from fastapi.responses import Response
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
