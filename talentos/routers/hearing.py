"""AIヒアリング（Dify連携 / モック対応）"""

from __future__ import annotations

import json
import os
import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from db.database import get_connection

router = APIRouter(prefix="/api/hearing", tags=["hearing"])

DIFY_API_KEY: str = os.getenv("DIFY_API_KEY", "")
DIFY_BASE_URL: str = os.getenv("DIFY_BASE_URL", "")

REQUIRED_FIELDS: dict[str, str] = {
    "basic": "専門分野、転勤可否、可能勤務地、最寄駅、最終学歴、学校名、学部・専攻名、学科名、自己PR、趣味特技、スキルレベル",
    "career": "プロジェクト名、期間（開始・終了）、チーム規模、役職・役割、使用技術、業務内容",
    "skills": "使用ツール、保有資格、語学力",
}

MOCK_QUESTIONS: dict[str, list[str]] = {
    "basic": [
        "ありがとうございます。転勤は可能ですか？希望の勤務地があれば教えてください。",
        "最寄り駅と、最終学歴（学校名・学部・学科）を教えていただけますか？",
        "自己PRを80文字以上でお聞かせください。趣味や特技もあればお願いします。",
        "IT系のスキルレベル（初級・中級・上級・エキスパート）を自己評価でお答えください。",
    ],
    "career": [
        "そのプロジェクトの期間（開始〜終了）を YYYY/MM 形式で教えてください。",
        "チームの規模と、あなたの役職・役割を教えてください。",
        "使用した技術スタック（言語、フレームワーク、ツール等）を教えてください。",
        "プロジェクトでの具体的な業務内容・成果を教えてください。",
    ],
    "skills": [
        "普段使用しているツール（IDE、バージョン管理、CI/CD等）を教えてください。",
        "保有している資格があれば教えてください。",
        "語学力について教えてください（言語名とレベル）。",
        "他に追加したいスキルや情報があれば教えてください。",
    ],
}

MOCK_EXTRACTED: dict[str, dict] = {
    "basic": {
        "specialty": "バックエンド開発",
        "relocation_ok": 1,
        "work_location": "東京都、リモート可",
        "nearest_station": "渋谷駅",
        "education_level": "大学卒",
        "school_name": "東京工業大学",
        "faculty_name": "情報理工学院",
        "department_name": "情報工学科",
        "self_pr": "バックエンド開発を中心に5年以上の経験があります。チームリーダーとしてプロジェクト推進も担当し、技術選定からアーキテクチャ設計まで幅広く対応できます。",
        "hobbies": "読書、ランニング",
        "skill_level": "上級",
    },
    "career": {
        "project_name": "金融システムAWS移行",
        "role_title": "テックリード",
        "team_size": 8,
        "period_start": "2023/04",
        "period_end": "2024/09",
        "tech_stack": ["AWS", "Terraform", "Python", "GitHub Actions"],
        "description": "オンプレミスからAWSへの移行をリードし、CI/CDパイプラインの構築を担当",
    },
    "skills": {
        "tools": ["VS Code", "Git", "Docker", "Terraform", "GitHub Actions"],
        "certifications": ["AWS Solutions Architect Associate", "基本情報技術者"],
        "language_skills": [
            {"language": "日本語", "level": "ネイティブ"},
            {"language": "英語", "level": "ビジネスレベル"},
        ],
    },
}


def _use_dify() -> bool:
    return bool(DIFY_API_KEY and DIFY_BASE_URL)


def _save_messages(engineer_id: str, theme: str, messages: list[dict], conversation_id: str, completed: bool) -> None:
    now: str = datetime.datetime.now().isoformat()
    conn = get_connection()
    row = conn.execute(
        "SELECT log_id FROM hearing_logs WHERE engineer_id = ? AND theme = ? AND completed = 0 ORDER BY log_id DESC LIMIT 1",
        (engineer_id, theme),
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE hearing_logs SET messages = ?, dify_conversation_id = ?, completed = ?, completed_at = ? WHERE log_id = ?",
            (json.dumps(messages, ensure_ascii=False), conversation_id, 1 if completed else 0, now if completed else None, row["log_id"]),
        )
    else:
        conn.execute(
            "INSERT INTO hearing_logs (engineer_id, theme, messages, dify_conversation_id, completed, completed_at) VALUES (?, ?, ?, ?, ?, ?)",
            (engineer_id, theme, json.dumps(messages, ensure_ascii=False), conversation_id, 1 if completed else 0, now if completed else None),
        )
    conn.commit()
    conn.close()


def _get_messages(engineer_id: str, theme: str) -> list[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT messages FROM hearing_logs WHERE engineer_id = ? AND theme = ? ORDER BY log_id DESC LIMIT 1",
        (engineer_id, theme),
    ).fetchone()
    conn.close()
    if row is None:
        return []
    return json.loads(row["messages"])


def _save_sheet(engineer_id: str, theme: str, raw_data: dict) -> None:
    now: str = datetime.datetime.now().isoformat()
    conn = get_connection()
    row = conn.execute(
        "SELECT sheet_id FROM skill_sheets WHERE engineer_id = ? AND theme = ?",
        (engineer_id, theme),
    ).fetchone()
    data_json: str = json.dumps(raw_data, ensure_ascii=False)
    if row:
        conn.execute(
            "UPDATE skill_sheets SET raw_data = ?, updated_at = ? WHERE sheet_id = ?",
            (data_json, now, row["sheet_id"]),
        )
    else:
        conn.execute(
            "INSERT INTO skill_sheets (engineer_id, theme, raw_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (engineer_id, theme, data_json, now, now),
        )
    conn.commit()
    conn.close()


class ChatRequest(BaseModel):
    theme: str
    message: str
    conversation_id: Optional[str] = ""


class OptimizeRequest(BaseModel):
    engineer_id: str


@router.post("/chat")
async def chat(body: ChatRequest, request: Request) -> dict:
    user: dict = request.state.user
    engineer_id: str = user["user_id"]
    theme: str = body.theme
    message: str = body.message
    conversation_id: str = body.conversation_id or ""

    # 既存メッセージ取得 & ユーザーメッセージ追加
    messages: list[dict] = _get_messages(engineer_id, theme)
    now: str = datetime.datetime.now().isoformat()
    messages.append({"role": "user", "content": message, "timestamp": now})

    if _use_dify():
        return await _dify_chat(engineer_id, theme, message, messages, conversation_id)
    else:
        return _mock_chat(engineer_id, theme, messages, conversation_id)


def _mock_chat(engineer_id: str, theme: str, messages: list[dict], conversation_id: str) -> dict:
    user_turns: int = sum(1 for m in messages if m.get("role") == "user")
    now: str = datetime.datetime.now().isoformat()
    conv_id: str = conversation_id or f"mock-{theme}-{engineer_id}"

    if user_turns >= 5:
        extracted: dict = MOCK_EXTRACTED.get(theme, {})
        theme_labels: dict[str, str] = {"basic": "基本情報", "career": "経歴", "skills": "スキル・資格"}
        ai_reply: str = f"{theme_labels.get(theme, theme)}のヒアリングが完了しました。次のステップに進みましょう。"
        messages.append({"role": "assistant", "content": ai_reply, "timestamp": now})
        _save_messages(engineer_id, theme, messages, conv_id, completed=True)
        _save_sheet(engineer_id, theme, extracted)
        return {
            "message": ai_reply,
            "theme_completed": True,
            "conversation_id": conv_id,
            "sheet_update": {"theme": theme, "data": extracted},
        }
    else:
        q_list: list[str] = MOCK_QUESTIONS.get(theme, ["もう少し詳しく教えてください。"])
        idx: int = min(user_turns - 1, len(q_list) - 1)
        ai_reply = q_list[idx]
        messages.append({"role": "assistant", "content": ai_reply, "timestamp": now})
        _save_messages(engineer_id, theme, messages, conv_id, completed=False)
        return {
            "message": ai_reply,
            "theme_completed": False,
            "sheet_update": None,
            "conversation_id": conv_id,
        }


async def _dify_chat(engineer_id: str, theme: str, user_message: str, messages: list[dict], conversation_id: str) -> dict:
    import httpx

    now: str = datetime.datetime.now().isoformat()
    payload: dict = {
        "query": user_message,
        "conversation_id": conversation_id,
        "inputs": {
            "theme": theme,
            "required_fields": REQUIRED_FIELDS.get(theme, ""),
        },
        "response_mode": "blocking",
        "user": engineer_id,
    }
    headers: dict = {"Authorization": f"Bearer {DIFY_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{DIFY_BASE_URL}/v1/chat-messages", json=payload, headers=headers)

        if resp.status_code >= 500:
            return {
                "message": "AI機能が一時的に利用できません。",
                "theme_completed": False,
                "conversation_id": conversation_id,
                "sheet_update": None,
            }

        data: dict = resp.json()
    except httpx.TimeoutException:
        return {
            "message": "AIの応答がタイムアウトしました。再度お試しください。",
            "theme_completed": False,
            "conversation_id": conversation_id,
            "sheet_update": None,
        }

    answer: str = data.get("answer", "")
    conv_id: str = data.get("conversation_id", conversation_id)
    theme_completed: bool = "theme_completed: true" in answer or "theme_completed:true" in answer

    messages.append({"role": "assistant", "content": answer, "timestamp": now})

    sheet_update: Optional[dict] = None
    if theme_completed:
        extracted: dict = {}
        try:
            start: int = answer.index("{")
            end: int = answer.rindex("}") + 1
            extracted = json.loads(answer[start:end])
        except (ValueError, json.JSONDecodeError):
            extracted = {"raw_answer": answer}
        _save_messages(engineer_id, theme, messages, conv_id, completed=True)
        _save_sheet(engineer_id, theme, extracted)
        sheet_update = {"theme": theme, "data": extracted}
    else:
        _save_messages(engineer_id, theme, messages, conv_id, completed=False)

    return {
        "message": answer,
        "theme_completed": theme_completed,
        "conversation_id": conv_id,
        "sheet_update": sheet_update,
    }


@router.post("/optimize")
async def optimize(body: OptimizeRequest, request: Request) -> dict:
    user: dict = request.state.user
    engineer_id: str = body.engineer_id

    if user["role"] == "engineer" and user["user_id"] != engineer_id:
        raise HTTPException(status_code=403, detail="自分のデータのみ操作できます")

    conn = get_connection()
    rows = conn.execute(
        "SELECT theme, raw_data FROM skill_sheets WHERE engineer_id = ?",
        (engineer_id,),
    ).fetchall()
    conn.close()

    raw_map: dict[str, dict] = {}
    for r in rows:
        raw_map[r["theme"]] = json.loads(r["raw_data"]) if r["raw_data"] else {}

    if _use_dify():
        optimized: dict = await _dify_optimize(engineer_id, raw_map)
    else:
        optimized = raw_map

    now: str = datetime.datetime.now().isoformat()
    conn = get_connection()
    for theme, data in optimized.items():
        conn.execute(
            "UPDATE skill_sheets SET optimized_data = ?, updated_at = ? WHERE engineer_id = ? AND theme = ?",
            (json.dumps(data, ensure_ascii=False), now, engineer_id, theme),
        )
    conn.commit()
    conn.close()

    return {"success": True, "optimized": optimized}


async def _dify_optimize(engineer_id: str, raw_map: dict[str, dict]) -> dict:
    import httpx

    payload: dict = {
        "inputs": {
            "basic_data": json.dumps(raw_map.get("basic", {}), ensure_ascii=False),
            "career_data": json.dumps(raw_map.get("career", {}), ensure_ascii=False),
            "skills_data": json.dumps(raw_map.get("skills", {}), ensure_ascii=False),
        },
        "response_mode": "blocking",
        "user": engineer_id,
    }
    headers: dict = {"Authorization": f"Bearer {DIFY_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{DIFY_BASE_URL}/v1/workflows/run", json=payload, headers=headers)

        if resp.status_code >= 500:
            return raw_map

        data: dict = resp.json()
    except httpx.TimeoutException:
        return raw_map

    outputs: dict = data.get("data", {}).get("outputs", {})
    try:
        return json.loads(outputs.get("result", "{}"))
    except (json.JSONDecodeError, TypeError):
        return raw_map
