"""Knowledge Base API — supports file upload and text paste."""
import tempfile
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.knowledge.service import upload_document, list_documents, delete_document, search_kb
from app.utils.file_parser import extract_text

router = APIRouter()


@router.post("/kb/upload")
async def kb_upload(
    file: UploadFile | None = File(None),
    content: str = Form(""),
    kb_type: str = Form("custom"),
    file_name: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document file or paste text to the knowledge base."""
    raw_text = ""
    fname = file_name

    if file:
        fname = file.filename or fname
        ALLOWED = {".pdf", ".docx", ".doc", ".txt", ".md"}
        ext = "." + fname.rsplit(".", 1)[-1].lower() if "." in fname else ".txt"
        if ext not in ALLOWED:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式 {ext}")

        file_bytes = await file.read()
        if len(file_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件过大，请上传小于 10MB 的文档")

        fd, tmp_path = tempfile.mkstemp(suffix=ext)
        import os
        os.close(fd)
        with open(tmp_path, "wb") as f:
            f.write(file_bytes)
        try:
            raw_text = extract_text(tmp_path, fname)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            os.unlink(tmp_path)
    elif content.strip():
        raw_text = content.strip()
        if not fname:
            fname = f"手动输入_{kb_type}"
    else:
        raise HTTPException(status_code=400, detail="请上传文件或粘贴文本内容")

    result = upload_document(db, current_user.id, kb_type, fname, raw_text,
                             file_type=ext if file else "txt")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "上传失败"))
    return result


@router.get("/kb/documents")
def kb_list(kb_type: str = Query("", description="Filter by type"),
            page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
            db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user)):
    return list_documents(db, current_user.id, kb_type, page, page_size)


@router.delete("/kb/documents/{doc_id}", status_code=204)
def kb_delete(doc_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    ok = delete_document(db, current_user.id, doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="文档不存在")


@router.post("/kb/documents/batch-delete", status_code=204)
def kb_batch_delete(ids: list[int], db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    from app.knowledge.models import KBDocument
    for doc_id in ids:
        delete_document(db, current_user.id, doc_id)
    db.commit()


@router.get("/kb/search")
def kb_search(q: str = Query(..., description="Search query"),
              kb_type: str = Query("", description="Filter by type"),
              db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    return search_kb(db, current_user.id, q, kb_type, top_k=10)
