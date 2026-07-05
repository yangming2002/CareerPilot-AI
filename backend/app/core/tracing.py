"""LangSmith tracing for LLM observability."""
import os

from app.core.config import OPENAI_API_KEY


def init_tracing():
    """Enable LangSmith tracing if API key is configured."""
    ls_key = os.getenv("LANGSMITH_API_KEY", "")
    if not ls_key:
        return

    os.environ.setdefault("LANGSMITH_PROJECT", "careerpilot-ai")
    os.environ.setdefault("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

    try:
        from langsmith import Client
        from langsmith.wrappers import wrap_openai
        import openai as openai_module

        # Wrap the OpenAI module for tracing
        wrap_openai(openai_module)
        Client()  # Verify connection
        from loguru import logger
        logger.info("LangSmith tracing enabled")
    except Exception as e:
        from loguru import logger
        logger.warning(f"LangSmith init failed (non-critical): {e}")
