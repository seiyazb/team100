"""FastAPI エントリポイント"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from typing import Union
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from starlette.types import ASGIApp, Receive, Scope, Send

from db.database import init_db
from routers import auth, skillsheet, hearing, search, users

load_dotenv()

app = FastAPI(title="TalentOS")

_secret_key: str | None = os.getenv("SECRET_KEY")
if not _secret_key:
    raise RuntimeError("SECRET_KEY が設定されていません。.env ファイルに SECRET_KEY を設定してください。")
app.state.secret_key = _secret_key
app.state.api_key = os.getenv("API_KEY", "")

# 静的ファイル・テンプレート
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ルーター登録
app.include_router(auth.router)
app.include_router(skillsheet.router)
app.include_router(hearing.router)
app.include_router(search.router)
app.include_router(users.router)


# --- セッション検証 + ロール制御ミドルウェア (純粋 ASGI) ---
PUBLIC_PATHS: set[str] = {"/login", "/api/auth/login", "/api/auth/logout", "/docs", "/openapi.json", "/redoc"}

PAGE_ROLES: dict[str, set[str]] = {
    "/hearing": {"engineer", "admin"},
    "/skillsheet": {"engineer", "sales", "admin"},
    "/search": {"sales", "admin"},
    "/users": {"admin"},
}


class SessionMiddleware:
    """純粋 ASGI ミドルウェア — BaseHTTPMiddleware のストリーム破損問題を回避"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope["path"]

        # 公開パス・静的ファイルはスキップ
        if path in PUBLIC_PATHS or path.startswith("/static"):
            await self.app(scope, receive, send)
            return

        # API キー認証（Dify 等の外部サービス向け）
        if path.startswith("/api/") and app.state.api_key:
            for key, value in scope.get("headers", []):
                if key == b"x-api-key" and value.decode("latin-1") == app.state.api_key:
                    scope.setdefault("state", {})
                    scope["state"]["user"] = {"user_id": "api", "name": "API", "role": "admin"}
                    await self.app(scope, receive, send)
                    return

        # Cookie からセッショントークンを取得
        headers: dict[str, str] = {}
        for key, value in scope.get("headers", []):
            if key == b"cookie":
                headers["cookie"] = value.decode("latin-1")
                break

        token: str | None = None
        cookie_str: str = headers.get("cookie", "")
        for part in cookie_str.split(";"):
            part = part.strip()
            if part.startswith("session="):
                token = part[len("session="):]
                break

        if token:
            serializer = URLSafeTimedSerializer(app.state.secret_key)
            try:
                data: dict = serializer.loads(token, max_age=8 * 60 * 60)
                # request.state.user にセットするために scope に埋め込む
                scope.setdefault("state", {})
                scope["state"]["user"] = data

                # ページレベルのロールチェック
                allowed_roles: set[str] | None = PAGE_ROLES.get(path)
                if allowed_roles and data.get("role") not in allowed_roles:
                    response = templates.TemplateResponse("forbidden.html", {
                        "request": Request(scope),
                        "user": data,
                    }, status_code=403)
                    await response(scope, receive, send)
                    return

                try:
                    await self.app(scope, receive, send)
                except Exception:
                    response = RedirectResponse(url="/login", status_code=302)
                    await response(scope, receive, send)
                return
            except (BadSignature, SignatureExpired):
                pass

        # 未認証 → ログインへリダイレクト
        response = RedirectResponse(url="/login", status_code=302)
        await response(scope, receive, send)


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


# --- 未定義パスの catch-all（全ルート定義の後に置くこと） ---
@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(request: Request, full_path: str) -> Response:
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    return RedirectResponse(url="/top", status_code=302)


# --- 起動時にDB初期化 ---
@app.on_event("startup")
async def on_startup() -> None:
    init_db()
