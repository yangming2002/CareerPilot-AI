"""LLM-based query rewriting: expand user query into multiple search variants."""
from app.llm.client import get_llm_client

REWRITE_PROMPT = """You are a search query optimizer. Given a user's JD search query, generate 3-5 alternative search queries that would help find relevant job descriptions.

Rules:
- Expand abbreviations (AI -> 人工智能, 大模型)
- Add synonyms (开发 -> 工程师, 编程)
- Add related skills (Python -> Python FastAPI Django)
- Generate queries in Chinese
- Keep each query under 30 characters

Return ONLY a JSON array of strings, no other text.

Example:
User query: "AI开发"
Output: ["AI应用开发工程师", "大模型Agent开发", "人工智能算法", "AI开发", "LLM应用开发"]

User query: {query}
Output:"""


def rewrite_query(query: str) -> list[str]:
    """Expand a user query into multiple search variants."""
    if not query or len(query.strip()) < 2:
        return [query] if query else []

    llm = get_llm_client()
    try:
        import json
        raw = llm.complete(
            system="You are a search query optimizer. Reply with ONLY a JSON array of strings.",
            user=REWRITE_PROMPT.format(query=query),
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
        variants = json.loads(raw)
        if isinstance(variants, list) and variants:
            # Always include original query
            if query not in variants:
                variants.insert(0, query)
            return variants[:5]
    except Exception:
        pass
    return [query]
