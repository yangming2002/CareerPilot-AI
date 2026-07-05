"""LLM-based query rewriting: expand user query into multiple search variants."""
from app.llm.client import get_llm_client

REWRITE_PROMPT = """You are a search query optimizer. Given a user's JD search query, generate 2-3 FOCUSED alternative search queries.

Rules:
- Generate queries in Chinese, each under 25 characters
- Stay CLOSE to the original intent — do NOT broaden the domain
- Only add direct synonyms and common abbreviations
- Do NOT add unrelated skills or change the job category
- Example: "AI Agent开发" → ["大模型Agent开发", "AI应用开发"] (stay in AI domain, don't add "Python后端")

User query: {query}
Output: (JSON array of 2-3 strings)"""


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
            return variants[:3]
    except Exception:
        pass
    return [query]
