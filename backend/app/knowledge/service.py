"""Knowledge Base service: upload, chunk, embed, index, search."""
from sqlalchemy.orm import Session
from app.knowledge.models import KBDocument, KBChunk
from app.memory import vector_store as vs
from loguru import logger


CHUNK_SIZE = 500  # characters per chunk
CHUNK_OVERLAP = 50


def upload_document(db: Session, user_id: int, kb_type: str,
                    file_name: str, raw_text: str, file_type: str = "txt") -> dict:
    """Upload a document, chunk it, embed, and index."""
    if len(raw_text.strip()) < 20:
        return {"success": False, "error": "文档内容过短"}

    # Save document
    doc = KBDocument(
        user_id=user_id, kb_type=kb_type,
        file_name=file_name, file_type=file_type,
        raw_text=raw_text, chunk_count=0,
    )
    db.add(doc)
    db.flush()

    # Chunk
    chunks = _chunk_text(raw_text, CHUNK_SIZE, CHUNK_OVERLAP)
    doc.chunk_count = len(chunks)
    db.commit()

    # Save chunks to SQL
    chunk_records = []
    for i, text in enumerate(chunks):
        c = KBChunk(document_id=doc.id, chunk_index=i, content=text,
                    token_count=len(text))
        db.add(c)
        chunk_records.append(c)
    db.commit()

    # Index chunks in Milvus
    try:
        vs.index_facts([{
            "text": c.content,
            "user_id": user_id,
            "category": f"kb_{kb_type}",
            "doc_id": f"kb_{doc.id}_chunk_{c.chunk_index}",
        } for c in chunk_records])
    except Exception as e:
        logger.warning(f"KB indexing failed: {e}")

    return {"success": True, "document_id": doc.id, "chunk_count": len(chunks)}


def search_kb(db: Session, user_id: int, query: str, kb_type: str = "",
              top_k: int = 5) -> list[dict]:
    """Search knowledge base with Milvus."""
    category = f"kb_{kb_type}" if kb_type else None
    return vs.search_similar_facts(query, user_id, category=category, top_k=top_k)


def list_documents(db: Session, user_id: int, kb_type: str = "",
                   page: int = 1, page_size: int = 50) -> dict:
    q = db.query(KBDocument).filter(KBDocument.user_id == user_id, KBDocument.status == "active")
    if kb_type:
        q = q.filter(KBDocument.kb_type == kb_type)
    total = q.count()
    docs = q.order_by(KBDocument.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{"id": d.id, "kb_type": d.kb_type, "file_name": d.file_name,
                   "file_type": d.file_type, "chunk_count": d.chunk_count,
                   "status": d.status, "created_at": str(d.created_at),
                   "preview": (d.raw_text or "")[:200]} for d in docs],
        "total": total, "page": page, "page_size": page_size,
    }


def delete_document(db: Session, user_id: int, doc_id: int) -> bool:
    """Soft delete a document and its chunks."""
    doc = db.query(KBDocument).filter(
        KBDocument.id == doc_id, KBDocument.user_id == user_id
    ).first()
    if not doc:
        return False
    doc.status = "deleted"
    # Remove from Milvus by doc_id filter
    try:
        vs.delete_user_facts(user_id)  # TODO: more targeted delete by doc_id
    except Exception:
        pass
    db.commit()
    return True


def _chunk_text(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks, trying to break at paragraph/sentence boundaries."""
    if len(text) <= size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            # Try to break at newline
            nl = text.rfind('\n', start, end)
            if nl > start + size // 2:
                end = nl + 1
            else:
                # Try to break at sentence end
                for sep in ['。', '！', '？', '.', '!', '?', '\n']:
                    pos = text.rfind(sep, start, end)
                    if pos > start + size // 2:
                        end = pos + 1
                        break
        chunks.append(text[start:end].strip())
        start = end - overlap if end < len(text) else len(text)
    return chunks
