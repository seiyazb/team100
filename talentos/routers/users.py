"""ユーザー管理（管理者用）"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from passlib.hash import bcrypt

from db.database import get_connection

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
async def list_users(request: Request) -> list[dict]:
    user = request.state.user
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="管理者のみアクセスできます")

    conn = get_connection()
    rows = conn.execute("SELECT user_id, name, role FROM users ORDER BY user_id").fetchall()
    conn.close()

    return [{"user_id": r["user_id"], "name": r["name"], "role": r["role"]} for r in rows]


class CreateUserRequest(BaseModel):
    user_id: str
    name: str
    role: str
    password: str


@router.post("")
async def create_user(body: CreateUserRequest, request: Request) -> dict:
    user = request.state.user
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="管理者のみアクセスできます")

    if body.role not in ("engineer", "sales", "admin"):
        raise HTTPException(status_code=400, detail="ロールは engineer, sales, admin のいずれかです")

    conn = get_connection()

    existing = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (body.user_id,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="このユーザーIDは既に使用されています")

    password_hash: str = bcrypt.hash(body.password)
    conn.execute(
        "INSERT INTO users (user_id, password_hash, name, role) VALUES (?, ?, ?, ?)",
        (body.user_id, password_hash, body.name, body.role),
    )

    if body.role == "engineer":
        conn.execute(
            "INSERT INTO engineers (engineer_id) VALUES (?)",
            (body.user_id,),
        )

    conn.commit()
    conn.close()

    return {"success": True, "user_id": body.user_id}
