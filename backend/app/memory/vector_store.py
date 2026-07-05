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

COLLECTION_NAME = "careerpilot_memory"


def _get_client() -> MilvusClient:
    """Get or create Milvus client. For prod: change to MilvusClient(uri='http://host:19530')."""
    client = MilvusClient(str(DB_PATH))

    # Auto-create collection on first use
    if COLLECTION_NAME not in client.list_collections():
        client.create_collection(
            collection_name=COLLECTION_NAME,
            dimension=DIM,
            metric_type="COSINE",
            auto_id=True,
        )
        # Add scalar indexes later if needed
    return client


def index_facts(facts: list[dict]) -> None:
    """
    Index facts into Milvus. Each fact should have:
    - text: the fact content (will be embedded)
    - user_id: int
    - category: str (skill/project/weakness/etc.)
    - doc_id: str (source identifier)
    """
    if not facts:
        return

    from app.memory.embeddings import embed_texts

    texts = [f["text"] for f in facts]
    vectors = embed_texts(texts)

    data = []
    for i, fact in enumerate(facts):
        data.append({
            "vector": vectors[i],
            "user_id": fact["user_id"],
            "category": fact.get("category", ""),
            "text": fact["text"][:1000],
            "doc_id": fact.get("doc_id", ""),
        })

    try:
        client = _get_client()
        client.insert(collection_name=COLLECTION_NAME, data=data)
        logger.debug(f"Indexed {len(facts)} facts into Milvus")
    except Exception as e:
        logger.warning(f"Milvus indexing failed (non-critical): {e}")


def search_similar(
    query: str,
    user_id: int,
    category: str | None = None,
    top_k: int = 10,
) -> list[dict]:
    """Search for facts similar to query, scoped to user."""
    from app.memory.embeddings import embed_text

    query_vec = embed_text(query)

    filter_expr = f'user_id == {user_id}'
    if category:
        filter_expr += f' && category == "{category}"'

    try:
        client = _get_client()
        results = client.search(
            collection_name=COLLECTION_NAME,
            data=[query_vec],
            limit=top_k,
            filter=filter_expr,
            output_fields=["text", "category", "doc_id"],
        )
        if results and results[0]:
            return [
                {"text": r["entity"]["text"], "category": r["entity"]["category"],
                 "score": round(r["distance"], 3)}
                for r in results[0]
            ]
    except Exception as e:
        logger.warning(f"Milvus search failed: {e}")

    return []


def delete_user_facts(user_id: int) -> None:
    """Remove all facts for a user (e.g., on account deletion)."""
    try:
        client = _get_client()
        client.delete(collection_name=COLLECTION_NAME, filter=f'user_id == {user_id}')
    except Exception as e:
        logger.warning(f"Milvus delete failed: {e}")
