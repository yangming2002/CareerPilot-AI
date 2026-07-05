"""Retrieve relevant user facts and JD history for a given analysis.

Architecture:
- JDs → Milvus vector search (many, diverse, need semantic similarity)
- User facts → SQL (few per user, structured query is sufficient)
- Hybrid: combine vector JD results + SQL fact results + keyword fallback
"""
from sqlalchemy.orm import Session

from app.memory import vector_store as vs
from app.memory.models import JDArchive, UserFact


class FactRetriever:
    """Search user memory: JDs via vector, facts via SQL, results merged."""

    def retrieve_for_jd(self, db: Session, user_id: int, jd_text: str,
                        jd_skills: list[str], limit: int = 10) -> dict:
        """Given a JD, retrieve relevant user facts, past JDs, and weaknesses."""
        query = " ".join(jd_skills) if jd_skills else jd_text[:500]

        # ── 1. Vector search: similar past JDs ──
        similar_jds = vs.search_similar_jds(query, user_id, top_k=5)

        # ── 2. Vector search: relevant user skills ──
        skills = vs.search_similar_facts(query, user_id, category="skill", top_k=limit)

        # ── 3. Vector search: relevant user projects ──
        projects = vs.search_similar_facts(query, user_id, category="project", top_k=limit)

        # ── 4. SQL: weaknesses (structured, chronological) ──
        weaknesses = self._find_weaknesses(db, user_id, limit)

        # ── 5. Keyword fallback: if vector returned nothing, try text match ──
        if not skills:
            skills = self._keyword_search_skills(db, user_id, query, limit)
        if not projects:
            projects = self._keyword_search_projects(db, user_id, query, limit)
        if not similar_jds:
            similar_jds = self._keyword_search_jds(db, user_id, query, 5)

        return {
            "relevant_skills": [{"content": s["text"], "score": s.get("score", 0)} for s in skills],
            "relevant_projects": [{"content": p["text"], "score": p.get("score", 0)} for p in projects],
            "similar_jds": [
                {"company": j.get("company", ""), "position": j.get("position", ""),
                 "match_score": j.get("match_score", 0), "score": j.get("score", 0),
                 "skills": j.get("skills", ""), "id": j.get("jd_id", 0)}
                for j in similar_jds
            ],
            "past_weaknesses": weaknesses,
            "user_profile": self._get_profile_summary(db, user_id),
        }

    # ── Keyword fallbacks ──

    def _keyword_search_skills(self, db, user_id, query, limit):
        facts = db.query(UserFact).filter(
            UserFact.user_id == user_id, UserFact.category == "skill"
        ).all()
        results = []
        q = query.lower()
        for f in facts:
            if any(w in f.content.lower() for w in q.split() if len(w) > 2):
                results.append({"text": f.content, "score": 1})
        return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

    def _keyword_search_projects(self, db, user_id, query, limit):
        facts = db.query(UserFact).filter(
            UserFact.user_id == user_id, UserFact.category == "project"
        ).all()
        results = []
        q = query.lower()
        for f in facts:
            if any(w in f.content.lower() for w in q.split() if len(w) > 2):
                results.append({"text": f.content[:300], "score": 1})
        return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

    def _keyword_search_jds(self, db, user_id, query, limit):
        archives = db.query(JDArchive).filter(
            JDArchive.user_id == user_id
        ).order_by(JDArchive.created_at.desc()).limit(50).all()
        results = []
        q = query.lower()
        for a in archives:
            score = 0
            for w in q.split():
                if len(w) > 2 and w in (a.tags or "").lower():
                    score += 3
                if len(w) > 2 and w in (a.jd_text or "").lower():
                    score += 1
            if score > 0:
                results.append({
                    "jd_id": a.id, "company": a.company or "", "position": a.position or "",
                    "match_score": a.match_score, "score": score, "skills": a.tags or "",
                })
        return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

    # ── SQL queries ──

    def _find_weaknesses(self, db: Session, user_id: int, limit: int):
        return (
            db.query(UserFact)
            .filter(UserFact.user_id == user_id, UserFact.category == "weakness")
            .order_by(UserFact.created_at.desc())
            .limit(limit).all()
        )

    def _get_profile_summary(self, db: Session, user_id: int) -> dict:
        return {
            "total_skills": db.query(UserFact).filter(
                UserFact.user_id == user_id, UserFact.category == "skill").count(),
            "total_projects": db.query(UserFact).filter(
                UserFact.user_id == user_id, UserFact.category == "project").count(),
            "total_weaknesses": db.query(UserFact).filter(
                UserFact.user_id == user_id, UserFact.category == "weakness").count(),
            "total_jds_analyzed": db.query(JDArchive).filter(
                JDArchive.user_id == user_id).count(),
        }
