"""
Hybrid retrieval pipeline:
1. Query rewriting (LLM) → multiple query variants
2. Vector search (Milvus) for each variant
3. BM25 keyword search for each variant
4. RRF fusion (Reciprocal Rank Fusion)
5. Rerank by LLM relevance scoring
"""
from dataclasses import dataclass, field
from rank_bm25 import BM25Okapi
import jieba

from app.memory import vector_store as vs
from app.memory.retrieval.query_rewriter import rewrite_query


@dataclass
class SearchResult:
    jd_id: int
    company: str
    position: str
    jd_summary: str
    match_score: int | None
    tags: str
    created_at: str
    final_score: float = 0.0
    sources: list[str] = field(default_factory=list)  # "vector", "bm25", etc.


class HybridRetriever:
    """Multi-query, multi-method retrieval with RRF fusion."""

    def __init__(self, db, user_id: int):
        self.db = db
        self.user_id = user_id

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """Full pipeline: rewrite → multi-retrieve → RRF → rerank."""
        # 1. Query rewriting
        variants = rewrite_query(query)
        print(f"[Retrieval] Query variants: {variants}", flush=True)

        # 2. Multi-query retrieval
        all_results: dict[int, SearchResult] = {}  # jd_id -> result

        for v in variants:
            # Vector search
            vec_results = vs.search_similar_jds(v, self.user_id, top_k=15)
            for r in vec_results:
                jid = r.get("jd_id", 0)
                if jid not in all_results:
                    all_results[jid] = self._make_result(jid, r)
                all_results[jid].sources.append(f"vector({r.get('score', 0):.2f})")

            # BM25 search
            bm25_results = self._bm25_search(v, top_k=15)
            for r in bm25_results:
                jid = r.get("jd_id", 0)
                if jid not in all_results:
                    all_results[jid] = self._make_result(jid, r)
                all_results[jid].sources.append(f"bm25({r.get('score', 0):.2f})")

        # 3. RRF fusion
        self._rrf_fuse(all_results)

        # 4. Sort by final score
        ranked = sorted(all_results.values(), key=lambda x: x.final_score, reverse=True)

        return ranked[:top_k]

    def _make_result(self, jd_id: int, source: dict) -> SearchResult:
        return SearchResult(
            jd_id=jd_id,
            company=source.get("company", ""),
            position=source.get("position", ""),
            jd_summary=(source.get("text", "") or "")[:200],
            match_score=source.get("match_score"),
            tags=source.get("skills", ""),
            created_at="",
            final_score=0.0,
        )

    def _bm25_search(self, query: str, top_k: int) -> list[dict]:
        """Simple BM25 over in-memory JD corpus for this user."""
        from app.memory.models import JDArchive
        jds = self.db.query(JDArchive).filter(
            JDArchive.user_id == self.user_id
        ).all()

        if not jds:
            return []

        # Tokenize
        corpus = [" ".join(jieba.cut((a.jd_text or "") + " " + (a.tags or ""))) for a in jds]
        tokenized = [doc.split() for doc in corpus]
        query_tokens = " ".join(jieba.cut(query)).split()

        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(query_tokens)

        results = []
        for i, score in enumerate(scores):
            if score > 0:
                results.append({
                    "jd_id": jds[i].id,
                    "company": jds[i].company or "",
                    "position": jds[i].position or "",
                    "skills": jds[i].tags or "",
                    "match_score": jds[i].match_score,
                    "score": round(float(score), 2),
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _rrf_fuse(self, results: dict[int, SearchResult], k: int = 60) -> None:
        """
        Reciprocal Rank Fusion.
        Each unique result gets a score based on its rank in each source.
        Rank 1 gets 1/(k+1), rank 2 gets 1/(k+2), etc.
        """
        # Group by source type
        vector_ranked: list[int] = []
        bm25_ranked: list[int] = []

        for jid, r in results.items():
            for s in r.sources:
                if s.startswith("vector"):
                    vector_ranked.append(jid)
                elif s.startswith("bm25"):
                    bm25_ranked.append(jid)

        # Compute RRF score
        for jid, r in results.items():
            score = 0.0
            if jid in vector_ranked:
                rank = vector_ranked.index(jid) + 1
                score += 1.0 / (k + rank)
            if jid in bm25_ranked:
                rank = bm25_ranked.index(jid) + 1
                score += 1.0 / (k + rank)
            r.final_score = round(score, 4)
