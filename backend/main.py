"""FastAPI主应用入口 - 知乎回答页A2A Demo."""

import asyncio
import json
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from dotenv import load_dotenv

from backend.agents.demo_orchestrator import DemoOrchestrator
from backend.models.schemas import (
    AskerType,
    CommentRequest,
    DemoPhase,
    PublishRequest,
    StartDemoRequest,
    StartDemoResponse,
)
from backend.services.zhihu_community import ZhihuCommunityClient
from backend.services.zhihu_oauth import ZhihuOAuthClient

load_dotenv("backend/.env")

orchestrator = DemoOrchestrator()
oauth_client = ZhihuOAuthClient()
community_client = ZhihuCommunityClient()
oauth_pending_states: set[str] = set()
oauth_sessions: dict[str, dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理."""
    print("🚀 知乎A2A社交创作助手 Demo 启动")
    yield
    print("🛑 知乎A2A社交创作助手 Demo 关闭")


app = FastAPI(
    title="知乎A2A社交创作助手",
    description="Agent-to-Agent社交交互创作辅助系统 - 知乎回答页Demo",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS配置
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "知乎A2A社交创作助手 API", "version": "2.0.0"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


def _oauth_redirect_uri(request: Request) -> str:
    return os.getenv("ZHIHU_OAUTH_REDIRECT_URI") or str(request.url_for("zhihu_oauth_callback"))


def _oauth_success_redirect() -> str:
    return os.getenv("ZHIHU_OAUTH_SUCCESS_REDIRECT", "/")


def _get_oauth_session(request: Request) -> dict[str, Any] | None:
    session_id = request.cookies.get("zhihu_oauth_session")
    if not session_id:
        return None
    return oauth_sessions.get(session_id)


@app.get("/api/auth/zhihu/login")
async def zhihu_oauth_login(request: Request):
    """跳转到知乎 OAuth 授权页."""
    state = secrets.token_urlsafe(16)
    oauth_pending_states.add(state)
    return RedirectResponse(
        oauth_client.build_authorize_url(
            redirect_uri=_oauth_redirect_uri(request),
            state=state,
        )
    )


@app.get("/api/auth/zhihu/callback")
async def zhihu_oauth_callback(
    request: Request,
    code: str = Query(default=""),
    state: str = Query(default=""),
):
    """知乎 OAuth 回调：code 换 access_token，并写入本地登录 session."""
    if not code:
        return JSONResponse({"error": "missing_code"}, status_code=400)
    if state and state not in oauth_pending_states:
        return JSONResponse({"error": "invalid_state"}, status_code=400)
    if state:
        oauth_pending_states.discard(state)

    token_data = await oauth_client.exchange_code(
        code=code,
        redirect_uri=_oauth_redirect_uri(request),
    )

    access_token = str(token_data.get("access_token", ""))
    try:
        userinfo = await oauth_client.get_userinfo(access_token)
    except Exception:
        userinfo = token_data.get("info") or {
            "uid": token_data.get("uid"),
            "fullname": "知乎用户",
        }

    session_id = secrets.token_urlsafe(24)
    oauth_sessions[session_id] = {
        "access_token": access_token,
        "token": token_data,
        "user": userinfo,
    }

    response = RedirectResponse(_oauth_success_redirect())
    response.set_cookie(
        "zhihu_oauth_session",
        session_id,
        httponly=True,
        samesite="lax",
        secure=os.getenv("APP_ENV") == "production",
        max_age=int(token_data.get("expires_in", 2592000)),
    )
    return response


@app.get("/api/auth/zhihu/me")
async def zhihu_oauth_me(request: Request):
    """返回当前知乎 OAuth 登录用户."""
    session = _get_oauth_session(request)
    if not session:
        return {"logged_in": False}
    return {
        "logged_in": True,
        "user": session.get("user") or {},
    }


@app.post("/api/auth/zhihu/logout")
async def zhihu_oauth_logout(request: Request):
    session_id = request.cookies.get("zhihu_oauth_session")
    if session_id:
        oauth_sessions.pop(session_id, None)
    response = JSONResponse({"status": "ok"})
    response.delete_cookie("zhihu_oauth_session")
    return response


async def _zhihu_oauth_proxy(
    request: Request,
    path_env: str,
    default_path: str,
    page: int,
    per_page: int,
):
    session = _get_oauth_session(request)
    if not session:
        return JSONResponse({"logged_in": False, "error": "not_authenticated"}, status_code=401)
    path = os.getenv(path_env, default_path)
    data = await oauth_client.get_authorized(
        path,
        str(session["access_token"]),
        {"page": page, "per_page": per_page},
    )
    return {"logged_in": True, "data": data}


@app.get("/api/auth/zhihu/following")
async def zhihu_oauth_following(
    request: Request,
    page: int = 0,
    per_page: int = 10,
):
    return await _zhihu_oauth_proxy(
        request,
        "ZHIHU_OAUTH_FOLLOWING_PATH",
        "/following",
        page,
        per_page,
    )


@app.get("/api/auth/zhihu/followers")
async def zhihu_oauth_followers(
    request: Request,
    page: int = 0,
    per_page: int = 10,
):
    return await _zhihu_oauth_proxy(
        request,
        "ZHIHU_OAUTH_FOLLOWERS_PATH",
        "/followers",
        page,
        per_page,
    )


@app.get("/api/auth/zhihu/mutuals")
async def zhihu_oauth_mutuals(
    request: Request,
    page: int = 0,
    per_page: int = 10,
):
    return await _zhihu_oauth_proxy(
        request,
        "ZHIHU_OAUTH_MUTUALS_PATH",
        "/mutuals",
        page,
        per_page,
    )


@app.get("/api/auth/zhihu/feed")
async def zhihu_oauth_feed(
    request: Request,
    page: int = 0,
    per_page: int = 10,
):
    return await _zhihu_oauth_proxy(
        request,
        "ZHIHU_OAUTH_FEED_PATH",
        "/feed",
        page,
        per_page,
    )


@app.get("/api/community/config")
async def zhihu_community_config():
    return {"configured": community_client.is_configured()}


@app.get("/api/community/ring/detail")
async def zhihu_ring_detail(request: Request):
    """代理知乎社区圈子详情，只做读取，不做自动发布."""
    path = os.getenv("ZHIHU_COMMUNITY_RING_DETAIL_PATH", "/openapi/ring/detail")
    return await community_client.get(path, dict(request.query_params))


@app.post("/api/demo/session/start", response_model=StartDemoResponse)
async def start_demo(req: StartDemoRequest):
    """启动Demo会话，开始写前分析."""
    session_id = orchestrator.create_session(
        question_title=req.question_title,
        question_desc=req.question_desc,
        asker_type=req.asker_type,
    )
    return StartDemoResponse(
        session_id=session_id,
        phase=DemoPhase.INIT,
        message="Demo会话创建成功，写前分析将在SSE事件流连接后启动",
    )


@app.get("/api/demo/session/{session_id}")
async def get_demo_session(session_id: str):
    """获取Demo会话状态."""
    session = orchestrator.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    return session.model_dump()


@app.post("/api/demo/session/{session_id}/publish")
async def publish_answer(session_id: str, req: PublishRequest):
    """模拟发布回答，生成提问者反馈."""
    session = orchestrator.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    await orchestrator.publish_and_feedback(session_id, req.draft_content)
    return {
        "status": "ok",
        "phase": session.phase,
        "feedback": session.publish_feedback.model_dump() if session.publish_feedback else {},
    }


@app.post("/api/demo/session/{session_id}/comment")
async def add_comment(session_id: str, req: CommentRequest):
    """提交答主评论回复，生成下一轮互动."""
    session = orchestrator.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    result = await orchestrator.comment_interaction(session_id, req.answerer_reply)
    return result


def format_sse_event(msg_type: str, payload: dict) -> str:
    """Format a server-sent event with the shared frontend message shape."""
    message = {
        "type": msg_type,
        "payload": payload,
        "timestamp": datetime.now().isoformat(),
    }
    data = json.dumps(message, ensure_ascii=False)
    return f"event: {msg_type}\ndata: {data}\n\n"


def format_flow_error(error: Exception) -> str:
    """把后端异常转换成可展示给用户的错误信息."""
    raw_message = str(error)
    lowered = raw_message.lower()

    if "invalid x-api-key" in lowered or "authentication_error" in lowered:
        return "LLM API Key 无效或未配置，请检查 backend/.env 中的 ANTHROPIC_API_KEY、ANTHROPIC_BASE_URL 和 MODEL_NAME 后重试。"

    return f"流程执行出错: {raw_message}"


@app.get("/api/demo/session/{session_id}/events")
async def demo_events(session_id: str, request: Request):
    """SSE：实时推送A2A Demo写前分析进度."""
    session = orchestrator.get_session(session_id)

    async def event_stream():
        if not session:
            yield format_sse_event("error", {"message": "Session not found"})
            return

        queue: asyncio.Queue[str] = asyncio.Queue()

        async def emit(msg_type: str, payload: dict):
            await queue.put(format_sse_event(msg_type, payload))

        yield format_sse_event("connected", {
            "message": "已连接，开始写前分析...",
            "session_id": session_id,
        })

        task = asyncio.create_task(
            orchestrator.run_pre_writing_analysis(
                session_id,
                progress_callback=emit,
            )
        )

        try:
            while True:
                if await request.is_disconnected():
                    task.cancel()
                    break

                try:
                    yield await asyncio.wait_for(queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    if task.done():
                        break
                    yield ": keep-alive\n\n"

            while not queue.empty():
                yield queue.get_nowait()

            await task
        except asyncio.CancelledError:
            raise
        except Exception as e:
            yield format_sse_event("error", {
                "message": format_flow_error(e),
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
