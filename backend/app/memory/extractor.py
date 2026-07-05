"""Extract facts from parsed resume and match results for long-term memory."""
from sqlalchemy.orm import Session

from app.llm.schemas import ParsedResumeFields
from app.memory.models import JDArchive, UserFact
from app.memory import vector_store as vs
from app.schemas.analysis import JDMatchResponse


class FactExtractor:
    """Extract structured facts from analysis results and store them."""

    def extract_from_resume(
        self, db: Session, user_id: int, fields: ParsedResumeFields, source: str = "resume"
    ) -> int:
        """Parse resume fields into UserFacts. Returns count of facts extracted."""
        count = 0

        # Skills
        for skill in fields.skills:
            if skill.strip():
                self._upsert_fact(db, user_id, "skill", skill.strip(), source, self._tag_skills([skill]))
                count += 1

        # Projects
        for proj in fields.projects:
            name = proj.get("name", "")
            desc = proj.get("description", "")
            if name:
                self._upsert_fact(db, user_id, "project",
                                  f"{name}: {desc[:200]}" if desc else name,
                                  source, self._tag_skills([name, desc]))
                count += 1

        # Education
        for edu in fields.education:
            school = edu.get("school", "")
            degree = edu.get("degree", "")
            if school:
                self._upsert_fact(db, user_id, "education",
                                  f"{degree} | {school}" if degree else school, source, "")
                count += 1

        # Internships
        for intern in fields.internships:
            company = intern.get("company", "")
            if company:
                self._upsert_fact(db, user_id, "internship",
                                  f"{company} | {intern.get('role', '')}", source, "")
                count += 1

        # Index into vector store for semantic search
        if count > 0:
            facts_data = []
            for f in db.query(UserFact).filter(
                UserFact.user_id == user_id, UserFact.source == source
            ).order_by(UserFact.created_at.desc()).limit(count).all():
                facts_data.append({
                    "text": f.content, "user_id": user_id,
                    "category": f.category, "doc_id": f.source,
                })
            vs.index_facts(facts_data)

        return count

    def extract_from_match(
        self, db: Session, user_id: int, response: JDMatchResponse,
        jd_text: str, source: str = "jd_match"
    ) -> None:
        """Store JD and match results. Also extract weakness facts from gaps."""
        # Archive the JD
        archive = JDArchive(
            user_id=user_id,
            company=self._guess_company(jd_text),
            position=self._guess_position(jd_text),
            jd_text=jd_text[:5000],
            jd_summary=response.jd_summary,
            required_skills=self._extract_missing_skills(response),
            match_score=response.match_score,
            tags=",".join([g.skill for g in response.skill_gaps if g.required and not g.user_has]),
        )
        db.add(archive)

        # Store weaknesses from gaps
        for gap in response.skill_gaps:
            if gap.required and not gap.user_has:
                self._upsert_fact(db, user_id, "weakness",
                                  f"缺少技能: {gap.skill} — {gap.note[:100]}",
                                  source, gap.skill)

        db.commit()

    def _upsert_fact(self, db: Session, user_id: int, category: str,
                     content: str, source: str, tags: str) -> None:
        """Insert or update a fact."""
        existing = (
            db.query(UserFact)
            .filter(UserFact.user_id == user_id, UserFact.category == category,
                    UserFact.content == content)
            .first()
        )
        if not existing:
            db.add(UserFact(
                user_id=user_id, category=category, content=content,
                source=source, tags=tags, confidence="auto"
            ))

    def _tag_skills(self, texts: list[str]) -> str:
        """Extract likely skill tags from text."""
        combined = " ".join(texts).lower()
        tech_keywords = [
            "python", "fastapi", "django", "docker", "kubernetes", "react", "vue",
            "typescript", "golang", "rust", "java", "c++", "sql", "mysql", "postgresql",
            "redis", "mongodb", "elasticsearch", "kafka", "rabbitmq", "grpc", "graphql",
            "langgraph", "langchain", "mcp", "agent", "rag", "llm", "nlp", "pytorch",
            "tensorflow", "spark", "hadoop", "aws", "azure", "gcp", "terraform",
            "jenkins", "git", "ci/cd", "linux", "sse", "websocket", "rest",
        ]
        found = [k for k in tech_keywords if k in combined]
        return ",".join(found[:10])

    def _extract_missing_skills(self, response: JDMatchResponse) -> str:
        return ",".join([
            g.skill for g in response.skill_gaps if g.required and not g.user_has
        ])

    def _guess_company(self, jd_text: str) -> str | None:
        """Simple heuristic to extract company name from JD."""
        import re
        patterns = [
            r'【(?:公司|企业)名称[：:]\s*(.+?)】',
            r'(?:公司|企业)[：:]\s*(.+?)[\n，。]',
            r'关于(.+?公司)',
        ]
        for p in patterns:
            m = re.search(p, jd_text)
            if m:
                return m.group(1).strip()[:200]
        return None

    def _guess_position(self, jd_text: str) -> str | None:
        import re
        patterns = [
            r'【?岗位(?:名称)?[：:]\s*(.+?)】?',
            r'(?:招聘|诚聘)(.+?)(?:工程师|经理|开发|设计|实习)',
        ]
        for p in patterns:
            m = re.search(p, jd_text)
            if m:
                return m.group(0).strip()[:200]
        return None
