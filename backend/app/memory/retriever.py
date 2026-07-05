"""Retrieve relevant user facts and JD history for a given analysis."""
from sqlalchemy.orm import Session

from app.memory import vector_store as vs
from app.memory.models import JDArchive, UserFact


class FactRetriever:
    """Search user memory for relevant facts and history using Milvus vector search."""

    def retrieve_for_jd(self, db: Session, user_id: int, jd_text: str, jd_skills: list[str], limit: int = 10) -> dict:
        """Given a JD, retrieve relevant user facts, past JDs, and weaknesses."""
        query = " ".join(jd_skills) if jd_skills else jd_text[:500]

        # Vector search across all categories
        all_results = vs.search_similar(query, user_id, top_k=limit * 2)

        skills = [r for r in all_results if r["category"] == "skill"][:limit]
        projects = [r for r in all_results if r["category"] == "project"][:limit]

        return {
            "relevant_skills": [{"content": s["text"], "score": s["score"]} for s in skills],
            "relevant_projects": [{"content": p["text"], "score": p["score"]} for p in projects],
            "past_weaknesses": self._find_weaknesses(db, user_id, jd_skills, 5),
            "similar_jds": self._find_similar_jds(db, user_id, jd_skills, 3),
            "user_profile": self._get_profile_summary(db, user_id),
        }

    def _find_weaknesses(self, db: Session, user_id: int, jd_skills: list[str], limit: int) -> list[dict]:
        """Find past weaknesses that match this JD's requirements."""
        return (
            db.query(UserFact)
            .filter(UserFact.user_id == user_id, UserFact.category == "weakness")
            .order_by(UserFact.created_at.desc())
            .limit(limit)
            .all()
        )

    def _find_similar_jds(self, db: Session, user_id: int, jd_skills: list[str], limit: int) -> list[dict]:
        """Find previously analyzed JDs with similar requirements."""
        archives = (
            db.query(JDArchive)
            .filter(JDArchive.user_id == user_id)
            .order_by(JDArchive.created_at.desc())
            .limit(50)
            .all()
        )
        results = []
        jd_lower = " ".join(jd_skills).lower()
        for a in archives:
            score = self._relevance_score(a.jd_text or "", a.tags or "", jd_lower)
            if score > 0:
                results.append({
                    "company": a.company or "未知公司",
                    "position": a.position or "未知岗位",
                    "match_score": a.match_score,
                    "similarity": score,
                    "id": a.id,
                })
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def _get_profile_summary(self, db: Session, user_id: int) -> dict:
        """Aggregate user profile from stored facts."""
        skills = (
            db.query(UserFact)
            .filter(UserFact.user_id == user_id, UserFact.category == "skill")
            .count()
        )
        projects = (
            db.query(UserFact)
            .filter(UserFact.user_id == user_id, UserFact.category == "project")
            .count()
        )
        weaknesses = (
            db.query(UserFact)
            .filter(UserFact.user_id == user_id, UserFact.category == "weakness")
            .count()
        )
        jds = db.query(JDArchive).filter(JDArchive.user_id == user_id).count()
        return {
            "total_skills": skills,
            "total_projects": projects,
            "total_weaknesses": weaknesses,
            "total_jds_analyzed": jds,
        }

    def _relevance_score(self, content: str, tags: str, query_lower: str) -> int:
        """Simple keyword overlap score."""
        if not query_lower:
            return 1
        score = 0
        content_lower = content.lower()
        tags_lower = tags.lower()
        for word in query_lower.split():
            if word in content_lower:
                score += 2
            if word in tags_lower:
                score += 3
        return score
