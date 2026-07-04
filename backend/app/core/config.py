import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env from backend/ directory
load_dotenv(BASE_DIR / ".env")

# ── Database ──
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'careerpilot.db'}")

# ── CORS ──
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

# ── JWT ──
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "careerpilot-dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))

# ── OpenAI ──
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "30"))
