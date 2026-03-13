"""AIヒアリング（Dify連携 / モック対応）"""

from __future__ import annotations

import json
import os
import re
import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from db.database import get_connection

router = APIRouter(prefix="/api/hearing", tags=["hearing"])

DIFY_BASE_URL: str = os.getenv("DIFY_BASE_URL", "")
DIFY_HEARING_API_KEY: str = os.getenv("DIFY_HEARING_API_KEY", "")
DIFY_OPTIMIZE_API_KEY: str = os.getenv("DIFY_OPTIMIZE_API_KEY", "")

REQUIRED_FIELDS: dict[str, str] = {
    "basic": "専門分野、転勤可否、可能勤務地、最寄駅、最終学歴（学校名・学部・学科）、自己PR（80文字以上）、趣味特技、スキルレベル",
    "career": "プロジェクト名、期間（開始・終了年月）、チーム規模（人数）、役職・役割、使用技術スタック、業務内容（80文字以上）",
    "skills": "語学力（言語名とレベル）、使用ツール、保有資格",
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
        "relocation_ok": False,
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
        "experiences": [
            {
                "project_name": "金融システムAWS移行プロジェクト",
                "period_start": "2023/04",
                "period_end": "2024/09",
                "team_size": 8,
                "role_title": "テックリード",
                "tech_stack": ["AWS", "Terraform", "Python", "GitHub Actions", "PostgreSQL"],
                "description": "オンプレミスで稼働していた金融システムのAWS移行を担当。インフラ設計からCI/CDパイプライン構築、本番切り替えまでを一貫してリード。無停止移行を実現し、運用コストを約30%削減。",
            }
        ]
    },
    "skills": {
        "language_skills": [
            {"language": "日本語", "level": "ネイティブ"},
            {"language": "英語", "level": "ビジネスレベル"},
        ],
        "tool_info": ["VS Code", "Git", "Docker", "Terraform", "GitHub Actions"],
        "certifications": ["AWS Solutions Architect Associate", "基本情報技術者"],
    },
}


def _use_dify_hearing() -> bool:
    return bool(DIFY_HEARING_API_KEY and DIFY_BASE_URL)


def _use_dify_optimize() -> bool:
    return bool(DIFY_OPTIMIZE_API_KEY and DIFY_BASE_URL)


def _extract_json_from_answer(answer: str) -> Optional[dict]:
    """Dify の返答から ```json ブロックを抽出してパースする"""
    pattern = r'```json\s*([\s\S]*?)\s*```'
    match = re.search(pattern, answer)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # フォールバック: 生の JSON を探す
    try:
        start: int = answer.index("{")
        end: int = answer.rindex("}") + 1
        return json.loads(answer[start:end])
    except (ValueError, json.JSONDecodeError):
        return None


def _clean_answer_for_display(answer: str) -> str:
    """返答から JSON ブロック・先頭の生JSONを除去して表示用テキストを返す"""
    # ```json ... ``` ブロックを除去
    cleaned: str = re.sub(r'```json\s*[\s\S]*?\s*```', '', answer).strip()
    # 先頭の JSON 配列/オブジェクトを除去（HTTPリクエストノードの出力混入対策）
    if cleaned.startswith("[") or cleaned.startswith("{"):
        bracket = "]" if cleaned.startswith("[") else "}"
        depth: int = 0
        end_pos: int = 0
        for i, ch in enumerate(cleaned):
            if ch in ("[", "{"):
                depth += 1
            elif ch in ("]", "}"):
                depth -= 1
                if depth == 0:
                    end_pos = i + 1
                    break
        if end_pos > 0:
            cleaned = cleaned[end_pos:].strip()
    return cleaned if cleaned else answer


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

    if _use_dify_hearing():
        return await _dify_chat(engineer_id, theme, message, messages, conversation_id)
    else:
        return _mock_chat(engineer_id, theme, messages, conversation_id)


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, request: Request) -> StreamingResponse:
    """ストリーミング対応チャットエンドポイント（SSE）"""
    user: dict = request.state.user
    engineer_id: str = user["user_id"]
    theme: str = body.theme
    message: str = body.message
    conversation_id: str = body.conversation_id or ""

    messages: list[dict] = _get_messages(engineer_id, theme)
    now: str = datetime.datetime.now().isoformat()
    messages.append({"role": "user", "content": message, "timestamp": now})

    if _use_dify_hearing():
        return StreamingResponse(
            _dify_chat_stream(engineer_id, theme, message, messages, conversation_id),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    else:
        result: dict = _mock_chat(engineer_id, theme, messages, conversation_id)

        async def mock_stream():
            # モック時は一括送信
            yield f"data: {json.dumps({'type': 'token', 'content': result['message']}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'conversation_id': result['conversation_id'], 'theme_completed': result['theme_completed'], 'sheet_update': result['sheet_update']}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            mock_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )


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
    headers: dict = {"Authorization": f"Bearer {DIFY_HEARING_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{DIFY_BASE_URL}/v1/chat-messages", json=payload, headers=headers)

        if resp.status_code >= 500:
            return {
                "message": "AI機能が一時的に利用できません。",
                "theme_completed": False,
                "conversation_id": conversation_id,
                "sheet_update": None,
            }

        data: dict = resp.json()
        print(f"[DEBUG] Dify chat response: {json.dumps(data, ensure_ascii=False, default=str)[:2000]}")
    except httpx.TimeoutException:
        return {
            "message": "AIの応答がタイムアウトしました。再度お試しください。",
            "theme_completed": False,
            "conversation_id": conversation_id,
            "sheet_update": None,
        }

    answer: str = data.get("answer", "")
    conv_id: str = data.get("conversation_id", conversation_id)

    # ```json ブロックから構造化データを抽出
    parsed: Optional[dict] = _extract_json_from_answer(answer)
    theme_completed: bool = bool(parsed and parsed.get("theme_completed"))

    # 表示用テキスト（JSONブロックを除去）
    display_message: str = _clean_answer_for_display(answer)
    messages.append({"role": "assistant", "content": display_message, "timestamp": now})

    sheet_update: Optional[dict] = None
    if theme_completed and parsed:
        extracted: dict = parsed.get("extracted_data", parsed)
        _save_messages(engineer_id, theme, messages, conv_id, completed=True)
        _save_sheet(engineer_id, theme, extracted)
        sheet_update = {"theme": theme, "data": extracted}
    else:
        _save_messages(engineer_id, theme, messages, conv_id, completed=False)

    return {
        "message": display_message,
        "theme_completed": theme_completed,
        "conversation_id": conv_id,
        "sheet_update": sheet_update,
    }


async def _dify_chat_stream(engineer_id: str, theme: str, user_message: str, messages: list[dict], conversation_id: str):
    """Dify ストリーミング API を SSE で中継するジェネレータ"""
    import httpx

    now: str = datetime.datetime.now().isoformat()
    payload: dict = {
        "query": user_message,
        "conversation_id": conversation_id,
        "inputs": {
            "theme": theme,
            "required_fields": REQUIRED_FIELDS.get(theme, ""),
        },
        "response_mode": "streaming",
        "user": engineer_id,
    }
    headers: dict = {"Authorization": f"Bearer {DIFY_HEARING_API_KEY}"}

    full_answer: str = ""
    conv_id: str = conversation_id
    in_json_block: bool = False
    json_buffer: str = ""

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", f"{DIFY_BASE_URL}/v1/chat-messages",
                json=payload, headers=headers,
            ) as resp:
                if resp.status_code >= 500:
                    yield f"data: {json.dumps({'type': 'token', 'content': 'AI機能が一時的に利用できません。'}, ensure_ascii=False)}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation_id, 'theme_completed': False, 'sheet_update': None}, ensure_ascii=False)}\n\n"
                    return

                buffer: str = ""
                stream_ended: bool = False
                async for chunk in resp.aiter_text():
                    if stream_ended:
                        break
                    buffer += chunk
                    while "\n\n" in buffer:
                        event_str, buffer = buffer.split("\n\n", 1)
                        # SSE イベントをパース
                        data_line: str = ""
                        for line in event_str.split("\n"):
                            if line.startswith("data: "):
                                data_line = line[6:]

                        if not data_line:
                            continue

                        try:
                            event_data: dict = json.loads(data_line)
                        except json.JSONDecodeError:
                            continue

                        event_type: str = event_data.get("event", "")

                        if event_type == "message":
                            delta: str = event_data.get("answer", "")
                            full_answer += delta
                            conv_id = event_data.get("conversation_id", conv_id)

                            # JSON ブロック・先頭 JSON をスキップして表示用テキストのみ送信
                            clean_delta: str = delta
                            # ```json ブロック内はスキップ
                            if "```json" in delta:
                                in_json_block = True
                                clean_delta = delta[:delta.index("```json")]
                            if in_json_block:
                                if "```" in delta and not delta.strip().startswith("```json"):
                                    in_json_block = False
                                    idx = delta.index("```") + 3
                                    clean_delta = delta[idx:]
                                else:
                                    clean_delta = ""

                            if clean_delta:
                                yield f"data: {json.dumps({'type': 'token', 'content': clean_delta}, ensure_ascii=False)}\n\n"

                        elif event_type == "message_end":
                            conv_id = event_data.get("conversation_id", conv_id)
                            stream_ended = True
                            break

    except httpx.TimeoutException:
        yield f"data: {json.dumps({'type': 'token', 'content': 'AIの応答がタイムアウトしました。再度お試しください。'}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation_id, 'theme_completed': False, 'sheet_update': None}, ensure_ascii=False)}\n\n"
        return
    except Exception:
        yield f"data: {json.dumps({'type': 'token', 'content': '通信エラーが発生しました。'}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation_id, 'theme_completed': False, 'sheet_update': None}, ensure_ascii=False)}\n\n"
        return

    # ストリーム完了後にDB保存・テーマ完了判定
    display_message: str = _clean_answer_for_display(full_answer)
    parsed: Optional[dict] = _extract_json_from_answer(full_answer)
    theme_completed: bool = bool(parsed and parsed.get("theme_completed"))

    messages.append({"role": "assistant", "content": display_message, "timestamp": now})

    sheet_update: Optional[dict] = None
    if theme_completed and parsed:
        extracted: dict = parsed.get("extracted_data", parsed)
        _save_messages(engineer_id, theme, messages, conv_id, completed=True)
        _save_sheet(engineer_id, theme, extracted)
        sheet_update = {"theme": theme, "data": extracted}
    else:
        _save_messages(engineer_id, theme, messages, conv_id, completed=False)

    yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id, 'theme_completed': theme_completed, 'sheet_update': sheet_update}, ensure_ascii=False)}\n\n"


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

    if _use_dify_optimize():
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
    headers: dict = {"Authorization": f"Bearer {DIFY_OPTIMIZE_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
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
