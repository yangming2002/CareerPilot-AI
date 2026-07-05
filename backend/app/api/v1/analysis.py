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
from app.core import progress as progress_store
from app.memory.extractor import FactExtractor
from app.memory.models import JDArchive, UserFact
from app.memory.retriever import FactRetriever
from app.services.analysis_service import AnalysisService
from app.services.graph_analysis_service import GraphAnalysisService
from app.services.llm_analysis_service import LLMAnalysisService
from app.services.match_postprocessor import MatchPostprocessor
from app.utils.file_parser import extract_text

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/analysis/progress/{session_id}")
def get_progress(session_id: str):
    data = progress_store.get_progress(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="进度会话不存在或已过期")
    return data


@router.get("/analysis/jd-history")
def jd_history(
    q: str = Query("", description="Search keyword"),
    engine: str = Query("hybrid", description="Search engine: 'hybrid' or 'sql'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search archived JDs with hybrid retrieval (vector + BM25 + RRF)."""
    # Hybrid pipeline
    if q and engine == "hybrid":
        try:
            from app.memory.retrieval.hybrid_retriever import HybridRetriever
            retriever = HybridRetriever(db, current_user.id)
            results = retriever.search(q, top_k=10)[:10]
            return [
                {
                    "id": r.jd_id, "company": r.company, "position": r.position,
                    "match_score": r.match_score,
                    "jd_summary": r.jd_summary or (r.jd_text[:300] if hasattr(r, 'jd_text') else ''),
                    "jd_text": r.jd_text if hasattr(r, 'jd_text') else r.jd_summary,
                    "tags": r.tags, "created_at": r.created_at,
                    "score": r.final_score, "sources": r.sources[:3],
                }
                for r in results
            ]
        except Exception:
            logger.exception("Hybrid search failed, falling back to SQL")

    # SQL fallback
    query = db.query(JDArchive).filter(JDArchive.user_id == current_user.id)
    if q:
        query = query.filter(
            (JDArchive.jd_text.contains(q)) |
            (JDArchive.company.contains(q)) |
            (JDArchive.position.contains(q)) |
            (JDArchive.tags.contains(q))
        )
    archives = query.order_by(JDArchive.created_at.desc()).limit(20).all()
    return [
        {
            "id": a.id, "company": a.company, "position": a.position,
            "match_score": a.match_score, "jd_summary": a.jd_summary or a.jd_text[:500],
            "jd_text": a.jd_text, "tags": a.tags, "created_at": str(a.created_at),
        }
        for a in archives
    ]


@router.get("/analysis/user-profile")
def user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's aggregated profile from memory."""
    retriever = FactRetriever()
    return retriever._get_profile_summary(db, current_user.id)


@router.get("/analysis/user-facts")
def list_user_facts(
    category: str = Query("", description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all extracted facts for the current user."""
    query = db.query(UserFact).filter(UserFact.user_id == current_user.id)
    if category:
        query = query.filter(UserFact.category == category)
    facts = query.order_by(UserFact.created_at.desc()).limit(100).all()
    return [
        {"id": f.id, "category": f.category, "content": f.content,
         "source": f.source, "confidence": f.confidence,
         "tags": f.tags, "created_at": str(f.created_at)}
        for f in facts
    ]


@router.delete("/analysis/user-facts/{fact_id}", status_code=204)
def delete_user_fact(
    fact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a single user fact."""
    fact = db.query(UserFact).filter(
        UserFact.id == fact_id, UserFact.user_id == current_user.id
    ).first()
    if not fact:
        raise HTTPException(status_code=404, detail="事实记录不存在")
    db.delete(fact)
    db.commit()


@router.post("/analysis/jd-match", response_model=JDMatchResponse)
def jd_match(
    body: JDMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = MatchPostprocessor()

    # ── Primary: Agent workflow ──
    sid = progress_store.create_session()
    try:
        result = GraphAnalysisService().analyze(
            db, body.resume_text, body.jd_text, current_user.id, session_id=sid
        )
        progress_store.push(sid, "分析完成")
        progress_store.mark_done(sid)
        response = post.process(result, body.jd_text, body.resume_text)
        response.session_id = sid
        _archive_analysis(db, current_user.id, response, body.jd_text, body.company, body.position, body.resume_text)
        return response

    except InputInsufficientError:
        raise
    except Exception:
        logger.exception("Agent workflow failed, falling back to single-shot LLM")

    # ── Fallback 1: Single-shot LLM ──
    try:
        result = LLMAnalysisService().analyze(db, body.resume_text, body.jd_text, current_user.id)
        response = post.process(result, body.jd_text, body.resume_text)
        response.degraded = True
        response.degraded_reason = "Agent 工作流异常，已降级为单次 LLM 分析（功能完整，仅流程简化）"
        _archive_analysis(db, current_user.id, response, body.jd_text, body.company, body.position, body.resume_text)
        return response

    except Exception:
        logger.exception("LLM also failed, falling back to rule engine")

    # ── Fallback 2: Rule engine ──
    result = AnalysisService().analyze(db, body.resume_text, body.jd_text, current_user.id)
    result.degraded = True
    result.degraded_reason = "Agent 和 LLM 均不可用，已切换为规则引擎（仅关键词匹配，建议稍后重试）"
    return post.process(result, body.jd_text, body.resume_text)


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
        revised_resume=report.revised_resume or "",
    )


@router.post("/analysis/parse-resume", response_model=ParsedResumeFields)
async def parse_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
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

        import os as _os
        fd, tmp_path = tempfile.mkstemp(suffix=ext)
        _os.close(fd)
        with open(tmp_path, "wb") as f:
            f.write(content)

        raw_text = extract_text(tmp_path, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("File parsing failed")
        raise HTTPException(status_code=422, detail=f"文件解析失败：{e}。请尝试直接粘贴简历内容。")
    finally:
        import os as _os2
        if 'tmp_path' in locals():
            _os2.unlink(tmp_path)

    if len(raw_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="文件解析后内容过短，可能文件为空白或仅为图片。请尝试直接粘贴简历内容。")

    # Parse with LLM — use plain completion (more reliable than json_object for complex schema)
    llm = get_llm_client()
    try:
        prompt = RESUME_PARSE_USER.format(resume_text=raw_text[:4000])
        raw_json = llm.complete(
            system=RESUME_PARSE_SYSTEM + "\nReply with ONLY a JSON object, no other text.",
            user=prompt,
        )
        import json as _json
        raw_json = raw_json.strip()
        if raw_json.startswith("```"):
            raw_json = raw_json.split("\n", 1)[-1]
            if raw_json.endswith("```"):
                raw_json = raw_json[:-3]
        data = _json.loads(raw_json)
        fields = ParsedResumeFields.model_validate(data)
        # Extract into memory
        try:
            extractor = FactExtractor()
            extractor.extract_from_resume(db, current_user.id, fields, source="resume_upload")
        except Exception:
            logger.exception("Fact extraction failed — non-critical")
        return fields
    except Exception as e:
        logger.exception("Resume parsing failed")
        return ParsedResumeFields(raw_summary=raw_text[:500])


@router.post("/analysis/rewrite-resume")
def rewrite_resume(
    body: JDMatchRequest,
    match_score: int = Query(..., description="Current match score"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a revised resume based on existing match analysis. Separate from main analysis for speed."""
    from app.llm.prompts import RESUME_REWRITE_SYSTEM, RESUME_REWRITE_USER

    llm = get_llm_client()
    try:
        result = llm.complete(
            system=RESUME_REWRITE_SYSTEM,
            user=RESUME_REWRITE_USER.format(
                resume_text=body.resume_text,
                jd_text=body.jd_text,
                match_score=match_score,
                gaps="",
                suggestions="",
                integrity="",
            ),
        )
        return {"revised_resume": result.strip()}
    except Exception as e:
        logger.exception("Resume rewrite failed")
        raise HTTPException(status_code=502, detail=f"简历改写失败：{e}")


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

    content = report.revised_resume or ""
    if not content.strip():
        content = "暂无改写内容，请先运行 LLM 分析并生成改写后的简历。"

    headers = {"Content-Disposition": "attachment; filename=revised_resume.md"}
    return PlainTextResponse(content=content, media_type="text/markdown", headers=headers)


@router.get("/analysis/export-pdf/{report_id}")
def export_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export revised resume as PDF with Chinese font support."""
    from fpdf import FPDF

    report = AnalysisService.get_report(db, report_id, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="分析报告不存在或无权访问")

    content = report.revised_resume or ""
    if not content.strip():
        content = "暂无改写内容，请先运行 LLM 分析并生成改写后的简历。"

    # Find a Chinese font
    import os as _os
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    font_path = ""
    for fp in font_paths:
        if _os.path.exists(fp):
            font_path = fp
            break

    pdf = FPDF()
    pdf.add_page()

    if font_path:
        pdf.add_font("CJK", "", font_path, uni=True)
        pdf.set_font("CJK", "", 11)
    else:
        pdf.set_font("Helvetica", "", 11)

    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.multi_cell(0, 7, content)

    pdf_bytes = pdf.output()
    headers = {"Content-Disposition": "attachment; filename=revised_resume.pdf"}
    from fastapi.responses import Response
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


# ── Analysis complete hook: archive facts ──

def _archive_analysis(db: Session, user_id: int, response: JDMatchResponse,
                      jd_text: str, company: str = "", position: str = "",
                      resume_text: str = "") -> None:
    """After a successful analysis, extract facts and archive the JD."""
    extractor = FactExtractor()
    try:
        extractor.extract_from_match(db, user_id, response, jd_text, company, position)
    except Exception:
        logger.exception("Fact archiving failed — non-critical")

    # Also extract resume facts for memory (covers manual paste, not just PDF upload)
    if resume_text and len(resume_text.strip()) >= 50:
        try:
            from app.llm.client import get_llm_client
            from app.llm.prompts import RESUME_PARSE_SYSTEM, RESUME_PARSE_USER
            from app.llm.schemas import ParsedResumeFields
            import json as _json

            llm = get_llm_client()
            prompt = RESUME_PARSE_USER.format(resume_text=resume_text[:4000])
            raw_json = llm.complete(
                system=RESUME_PARSE_SYSTEM + "\nReply with ONLY a JSON object, no other text.",
                user=prompt,
            )
            raw_json = raw_json.strip()
            if raw_json.startswith("```"):
                raw_json = raw_json.split("\n", 1)[-1]
                if raw_json.endswith("```"):
                    raw_json = raw_json[:-3]
            fields = ParsedResumeFields.model_validate(_json.loads(raw_json))
            extractor.extract_from_resume(db, user_id, fields, source="jd_match_auto")
            logger.info(f"Auto-extracted facts from resume for user {user_id}")
        except Exception:
            logger.exception("Auto fact extraction failed — non-critical")
