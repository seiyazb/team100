"""ログイン・ログアウト"""

import json
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from passlib.hash import bcrypt
from itsdangerous import URLSafeTimedSerializer

from db.database import get_connection

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    user_id: str
    password: str


def _get_serializer(request: Request) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(request.app.state.secret_key)


@router.post("/login")
async def login(body: LoginRequest, request: Request, response: Response) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT user_id, password_hash, name, role FROM users WHERE user_id = ?",
        (body.user_id,),
    ).fetchone()
    conn.close()

    if row is None or not bcrypt.verify(body.password, row["password_hash"]):
        return {"success": False, "message": "IDまたはパスワードが正しくありません"}

    serializer = _get_serializer(request)
    token = serializer.dumps({
        "user_id": row["user_id"],
        "name": row["name"],
        "role": row["role"],
    })

    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        max_age=8 * 60 * 60,  # 8時間
        samesite="strict",
    )

    return {"success": True, "role": row["role"], "name": row["name"]}


@router.post("/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie("session")
    response.status_code = 302
    response.headers["Location"] = "/login"
    return {}
