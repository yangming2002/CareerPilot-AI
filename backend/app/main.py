from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import router as v1_router
from app.core.config import CORS_ORIGINS
from app.core.database import Base, engine

# Ensure all models are imported for table creation
import app.models.models  # noqa: F401
import app.models.user  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="CareerPilot-AI",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handlers ──

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Translate Pydantic 422 errors to user-friendly Chinese messages."""
    messages: list[str] = []
    for error in exc.errors():
        loc = error.get("loc", [])
        field = loc[-1] if loc else ""
        msg = error.get("msg", "")

        if field == "resume_text":
            if "min_length" in str(msg):
                messages.append("简历内容过短，请至少填写包含技能和工作经历的完整简历。")
            else:
                messages.append("简历内容格式有误，请检查后重新填写。")
        elif field == "jd_text":
            if "min_length" in str(msg):
                messages.append("JD 内容过短，请粘贴完整的岗位描述。")
            else:
                messages.append("JD 内容格式有误，请检查后重新填写。")
        elif field == "password":
            if "min_length" in str(msg):
                messages.append("密码至少需要 6 位。")
            elif "max_length" in str(msg):
                messages.append("密码过长，请控制在 128 位以内。")
            else:
                messages.append("密码格式有误。")
        elif field == "email":
            messages.append("请输入有效的邮箱地址。")
        elif field == "username":
            if "min_length" in str(msg):
                messages.append("用户名不能为空。")
            elif "max_length" in str(msg):
                messages.append("用户名过长，请控制在 100 字以内。")
            else:
                messages.append("用户名格式有误。")
        elif field == "company":
            messages.append("公司名称过长，请控制在 200 字以内。")
        elif field == "position":
            messages.append("岗位名称过长，请控制在 200 字以内。")
        elif field == "round":
            messages.append("面试轮次名称过长。")
        else:
            # Generic fallback — still in Chinese
            messages.append(f"「{field}」字段填写有误，请检查后重试。")

    detail = "；".join(messages) if messages else "请求数据格式有误，请检查后重试。"
    return JSONResponse(status_code=422, content={"detail": detail})


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Generic 500 — never leak stack traces."""
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试。如持续出现请切换规则引擎或联系管理员。"},
    )


# ── Routers ──
app.include_router(v1_router)


@app.get("/health")
def health():
    return {"status": "ok"}
