"""FastAPI エントリポイント"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from starlette.middleware.base import BaseHTTPMiddleware

from db.database import init_db
from routers import auth, skillsheet, hearing, search, users

load_dotenv()

app = FastAPI(title="TalentOS")

_secret_key: str | None = os.getenv("SECRET_KEY")
if not _secret_key:
    raise RuntimeError("SECRET_KEY が設定されていません。.env ファイルに SECRET_KEY を設定してください。")
app.state.secret_key = _secret_key

# 静的ファイル・テンプレート
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ルーター登録
app.include_router(auth.router)
app.include_router(skillsheet.router)
app.include_router(hearing.router)
app.include_router(search.router)
app.include_router(users.router)


# --- セッション検証 + ロール制御ミドルウェア ---
PUBLIC_PATHS: set[str] = {"/login", "/api/auth/login", "/api/auth/logout"}

# ページパスごとのアクセス許可ロール
PAGE_ROLES: dict[str, set[str]] = {
    "/hearing": {"engineer", "admin"},
    "/skillsheet": {"engineer", "sales", "admin"},
    "/search": {"sales", "admin"},
    "/users": {"admin"},
}


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path: str = request.url.path

        # 公開パス・静的ファイルはスキップ
        if path in PUBLIC_PATHS or path.startswith("/static"):
            return await call_next(request)

        # Cookie からセッション検証
        token: str | None = request.cookies.get("session")
        if token:
            serializer = URLSafeTimedSerializer(app.state.secret_key)
            try:
                data: dict = serializer.loads(token, max_age=8 * 60 * 60)
                request.state.user = data

                # ページレベルのロールチェック
                allowed_roles: set[str] | None = PAGE_ROLES.get(path)
                if allowed_roles and data.get("role") not in allowed_roles:
                    return templates.TemplateResponse("forbidden.html", {
                        "request": request,
                        "user": data,
                    }, status_code=403)

                return await call_next(request)
            except (BadSignature, SignatureExpired):
                pass

        # 未認証 → ログインへリダイレクト
        return RedirectResponse(url="/login", status_code=302)


app.add_middleware(SessionMiddleware)


# --- ページルート ---
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/top")
async def top_page(request: Request) -> RedirectResponse:
    role: str = request.state.user.get("role", "engineer")
    redirect_map: dict[str, str] = {
        "engineer": "/hearing",
        "sales": "/search",
        "admin": "/users",
    }
    return RedirectResponse(url=redirect_map.get(role, "/login"), status_code=302)


@app.get("/hearing", response_class=HTMLResponse)
async def hearing_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("ai-hearing.html", {
        "request": request,
        "user": request.state.user,
    })


@app.get("/skillsheet", response_class=HTMLResponse)
async def skillsheet_page(request: Request, engineer_id: str = "") -> HTMLResponse:
    user: dict = request.state.user
    target_id: str = engineer_id if engineer_id else user.get("user_id", "")
    return templates.TemplateResponse("skillsheet.html", {
        "request": request,
        "user": user,
        "target_engineer_id": target_id,
    })


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("search.html", {
        "request": request,
        "user": request.state.user,
    })


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("users.html", {
        "request": request,
        "user": request.state.user,
    })


# --- 起動時にDB初期化 ---
@app.on_event("startup")
async def on_startup() -> None:
    init_db()
