"""
Milvus vector store for semantic search.
Uses Milvus Lite (local file) for dev; switch to Milvus Standalone URI for production.
"""
import logging
from pathlib import Path

from pymilvus import DataType, MilvusClient

from app.memory.embeddings import DIM

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent.parent / "careerpilot_milvus.db"

FACTS_COLLECTION = "user_facts"
JD_COLLECTION = "jd_archive"


def _get_client() -> MilvusClient:
    """Get or create Milvus client. For prod: change to MilvusClient(uri='http://host:19530')."""
    client = MilvusClient(str(DB_PATH))

    for coll in [FACTS_COLLECTION, JD_COLLECTION]:
        if coll not in client.list_collections():
            client.create_collection(
                collection_name=coll,
                dimension=DIM,
                metric_type="COSINE",
                auto_id=True,
            )
    return client


def _insert_batch(collection: str, records: list[dict]) -> None:
    """Insert records into a Milvus collection with embeddings."""
    if not records:
        return
    from app.memory.embeddings import embed_texts

    texts = [r["text"] for r in records]
    vectors = embed_texts(texts)

    data = []
    for i, rec in enumerate(records):
        row = {"vector": vectors[i], "text": rec["text"][:2000]}
        for k, v in rec.items():
            if k != "text" and k != "vector":
                row[k] = v
        data.append(row)

    try:
        client = _get_client()
        client.insert(collection_name=collection, data=data)
        logger.debug(f"Inserted {len(records)} records into {collection}")
    except Exception as e:
        logger.warning(f"Milvus insert failed for {collection}: {e}")


# ── User Facts ──

def index_facts(facts: list[dict]) -> None:
    """Index user facts (skills, projects) into Milvus. Low volume, few per user."""
    records = []
    for f in facts:
        records.append({
            "text": f["text"][:1000],
            "user_id": f["user_id"],
            "category": f.get("category", ""),
            "doc_id": f.get("doc_id", ""),
        })
    _insert_batch(FACTS_COLLECTION, records)


def search_similar_facts(
    query: str, user_id: int, category: str | None = None, top_k: int = 10,
) -> list[dict]:
    """Vector search user facts."""
    from app.memory.embeddings import embed_text

    query_vec = embed_text(query)
    filter_expr = f'user_id == {user_id}'
    if category:
        filter_expr += f' && category == "{category}"'

    try:
        client = _get_client()
        results = client.search(
            collection_name=FACTS_COLLECTION, data=[query_vec],
            limit=top_k, filter=filter_expr,
            output_fields=["text", "category", "doc_id"],
        )
        if results and results[0]:
            return [
                {"text": r["entity"]["text"], "category": r["entity"]["category"],
                 "score": round(r["distance"], 3)}
                for r in results[0]
            ]
    except Exception as e:
        logger.warning(f"Facts search failed: {e}")
    return []


# ── JD Archive ──

def index_jd(jd: dict) -> None:
    """
    Index a JD into Milvus.
    jd: {text: JD全文, user_id, jd_id, company, position, skills, match_score}
    """
    _insert_batch(JD_COLLECTION, [jd])


def search_similar_jds(
    query: str, user_id: int, top_k: int = 10,
) -> list[dict]:
    """Vector search past JDs for similarity to current query."""
    from app.memory.embeddings import embed_text

    query_vec = embed_text(query)
    try:
        client = _get_client()
        results = client.search(
            collection_name=JD_COLLECTION, data=[query_vec],
            limit=top_k, filter=f'user_id == {user_id}',
            output_fields=["text", "company", "position", "skills", "match_score", "jd_id"],
        )
        if results and results[0]:
            return [
                {
                    "jd_id": r["entity"].get("jd_id", 0),
                    "company": r["entity"].get("company", ""),
                    "position": r["entity"].get("position", ""),
                    "skills": r["entity"].get("skills", ""),
                    "match_score": r["entity"].get("match_score", 0),
                    "score": round(r["distance"], 3),
                }
                for r in results[0]
            ]
    except Exception as e:
        logger.warning(f"JD search failed: {e}")
    return []


def delete_user_facts(user_id: int) -> None:
    try:
        client = _get_client()
        for coll in [FACTS_COLLECTION, JD_COLLECTION]:
            client.delete(collection_name=coll, filter=f'user_id == {user_id}')
    except Exception as e:
        logger.warning(f"Milvus delete failed: {e}")
