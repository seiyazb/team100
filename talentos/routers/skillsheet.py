"""スキルシートCRUD + PDF出力"""

from __future__ import annotations

import json
import datetime
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

from db.database import get_connection

router = APIRouter(prefix="/api/skillsheet", tags=["skillsheet"])


def _build_sheet_response(engineer_id: str) -> Optional[dict]:
    conn = get_connection()

    user_row = conn.execute(
        "SELECT user_id, name, role FROM users WHERE user_id = ?", (engineer_id,)
    ).fetchone()
    if not user_row:
        conn.close()
        return None

    eng_row = conn.execute(
        "SELECT * FROM engineers WHERE engineer_id = ?", (engineer_id,)
    ).fetchone()

    sheets = conn.execute(
        "SELECT theme, raw_data, optimized_data FROM skill_sheets WHERE engineer_id = ?",
        (engineer_id,),
    ).fetchall()

    exps = conn.execute(
        "SELECT * FROM experiences WHERE engineer_id = ? ORDER BY period_start DESC",
        (engineer_id,),
    ).fetchall()

    conn.close()

    basic_data: dict = {}
    skills_data: dict = {}
    optimized: dict = {}
    career_from_sheet: Optional[dict] = None

    for s in sheets:
        raw = json.loads(s["raw_data"]) if s["raw_data"] else {}
        opt = json.loads(s["optimized_data"]) if s["optimized_data"] else {}
        if s["theme"] == "basic":
            basic_data = raw
        elif s["theme"] == "career":
            career_from_sheet = raw
        elif s["theme"] == "skills":
            skills_data = raw
        if opt:
            optimized[s["theme"]] = opt

    career_list: list[dict] = []
    if career_from_sheet and isinstance(career_from_sheet, dict) and career_from_sheet.get("project_name"):
        career_list.append(career_from_sheet)

    for e in exps:
        ts = json.loads(e["tech_stack"]) if e["tech_stack"] else []
        career_list.append({
            "project_name": e["project_name"],
            "period_start": e["period_start"],
            "period_end": e["period_end"],
            "team_size": e["team_size"],
            "role_title": e["role_title"],
            "tech_stack": ts,
            "description": e["description"],
        })

    specialty = basic_data.get("specialty", "")
    if eng_row and eng_row["specialty"]:
        specialty = eng_row["specialty"]

    return {
        "engineer_id": engineer_id,
        "name": user_row["name"],
        "specialty": specialty,
        "basic": basic_data,
        "career": career_list,
        "skills": skills_data,
        "optimized": optimized,
    }


@router.get("/{engineer_id}")
async def get_skillsheet(engineer_id: str, request: Request) -> dict:
    user = request.state.user
    if user["role"] == "engineer" and user["user_id"] != engineer_id:
        raise HTTPException(status_code=403, detail="自分のスキルシートのみ閲覧できます")

    data = _build_sheet_response(engineer_id)
    if data is None:
        raise HTTPException(status_code=404, detail="エンジニアが見つかりません")
    return data


class SaveRequest(BaseModel):
    engineer_id: str
    basic: Optional[dict] = None
    career: Optional[list] = None
    skills: Optional[dict] = None


@router.post("/save")
async def save_skillsheet(body: SaveRequest, request: Request) -> dict:
    user = request.state.user
    engineer_id = body.engineer_id

    if user["role"] == "engineer" and user["user_id"] != engineer_id:
        raise HTTPException(status_code=403, detail="自分のスキルシートのみ編集できます")

    now = datetime.datetime.now().isoformat()

    try:
        conn = get_connection()

        for theme, data in [("basic", body.basic), ("career", body.career), ("skills", body.skills)]:
            if data is None:
                continue
            data_json = json.dumps(data, ensure_ascii=False)
            row = conn.execute(
                "SELECT sheet_id FROM skill_sheets WHERE engineer_id = ? AND theme = ?",
                (engineer_id, theme),
            ).fetchone()
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

        if body.basic:
            b = body.basic
            eng_row = conn.execute("SELECT engineer_id FROM engineers WHERE engineer_id = ?", (engineer_id,)).fetchone()
            if eng_row:
                conn.execute(
                    "UPDATE engineers SET specialty=?, relocation_ok=?, work_location=?, nearest_station=?,"
                    " education_level=?, school_name=?, faculty_name=?, department_name=?,"
                    " self_pr=?, hobbies=?, skill_level=?, updated_at=? WHERE engineer_id=?",
                    (b.get("specialty"), b.get("relocation_ok", 0), b.get("work_location"),
                     b.get("nearest_station"), b.get("education_level"), b.get("school_name"),
                     b.get("faculty_name"), b.get("department_name"), b.get("self_pr"),
                     b.get("hobbies"), b.get("skill_level"), now, engineer_id),
                )
            else:
                conn.execute(
                    "INSERT INTO engineers (engineer_id, specialty, relocation_ok, work_location, nearest_station,"
                    " education_level, school_name, faculty_name, department_name, self_pr, hobbies, skill_level, updated_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (engineer_id, b.get("specialty"), b.get("relocation_ok", 0), b.get("work_location"),
                     b.get("nearest_station"), b.get("education_level"), b.get("school_name"),
                     b.get("faculty_name"), b.get("department_name"), b.get("self_pr"),
                     b.get("hobbies"), b.get("skill_level"), now),
                )

        conn.commit()
        conn.close()
        return {"success": True}
    except Exception:
        raise HTTPException(status_code=500, detail="データの保存に失敗しました。")


@router.get("/{engineer_id}/pdf")
async def get_pdf(engineer_id: str, request: Request) -> Response:
    user = request.state.user
    if user["role"] == "engineer" and user["user_id"] != engineer_id:
        raise HTTPException(status_code=403, detail="自分のスキルシートのみ出力できます")

    data = _build_sheet_response(engineer_id)
    if data is None:
        raise HTTPException(status_code=404, detail="エンジニアが見つかりません")

    html_content = _render_pdf_html(data)

    try:
        from weasyprint import HTML
        pdf_bytes: bytes = HTML(string=html_content).write_pdf()
    except ImportError:
        return Response(
            content=html_content.encode("utf-8"),
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="skillsheet_{engineer_id}.html"'},
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="skillsheet_{engineer_id}.pdf"'},
    )


def _render_pdf_html(data: dict) -> str:
    basic: dict = data.get("basic", {})
    career_list: list = data.get("career", [])
    skills: dict = data.get("skills", {})

    all_skills: list[str] = []
    for c in career_list:
        all_skills.extend(c.get("tech_stack", []))
    all_skills.extend(skills.get("tools", []))
    all_skills.extend(skills.get("languages", []))
    unique_skills: list[str] = list(dict.fromkeys(all_skills))

    career_html: str = ""
    for c in career_list:
        ts = ", ".join(c.get("tech_stack", []))
        career_html += (
            '<div style="margin-bottom:16px; padding:12px; border:1px solid #ddd; border-radius:6px;">'
            '<div style="display:flex; justify-content:space-between;">'
            f'<strong>{_esc(c.get("project_name",""))}</strong>'
            f'<span>{_esc(c.get("period_start",""))} 〜 {_esc(c.get("period_end",""))}</span>'
            '</div>'
            f'<div style="margin:6px 0; color:#555;">役職：{_esc(c.get("role_title",""))}　チーム規模：{c.get("team_size","")}名</div>'
            f'<div style="margin:4px 0; color:#666;">技術：{_esc(ts)}</div>'
            f'<div style="margin-top:6px;">{_esc(c.get("description",""))}</div>'
            '</div>'
        )

    certs: list = skills.get("certifications", [])
    certs_html: str = ", ".join(certs) if certs else "—"
    langs: list = skills.get("language_skills", [])
    langs_html: str = ", ".join(f'{l.get("language","")}: {l.get("level","")}' for l in langs) if langs else "—"

    skill_tags: str = "".join(f'<span class="skill-tag">{_esc(s)}</span>' for s in unique_skills)

    return (
        '<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><style>'
        'body { font-family: "Noto Sans JP", "Hiragino Sans", sans-serif; margin: 40px; color: #1c1917; font-size: 13px; line-height: 1.7; }'
        'h1 { font-size: 20px; border-bottom: 3px solid #f97316; padding-bottom: 8px; margin-bottom: 24px; }'
        'h2 { font-size: 15px; color: #ea580c; margin: 20px 0 10px; border-left: 4px solid #f97316; padding-left: 10px; }'
        '.info-row { display: flex; gap: 8px; margin: 4px 0; }'
        '.info-label { font-weight: 600; min-width: 100px; }'
        '.skills-tags { display: flex; flex-wrap: wrap; gap: 6px; }'
        '.skill-tag { background: #fff7ed; border: 1px solid #fed7aa; color: #ea580c; padding: 2px 10px; border-radius: 4px; font-size: 12px; }'
        '</style></head><body>'
        f'<h1>【スキルシート】{_esc(data.get("name",""))}</h1>'
        '<h2>基本情報</h2>'
        f'<div class="info-row"><span class="info-label">専門分野：</span><span>{_esc(data.get("specialty",""))}</span></div>'
        f'<div class="info-row"><span class="info-label">最終学歴：</span><span>{_esc(basic.get("school_name",""))} {_esc(basic.get("faculty_name",""))}</span></div>'
        f'<div class="info-row"><span class="info-label">勤務地：</span><span>{_esc(basic.get("work_location",""))}</span></div>'
        f'<div class="info-row"><span class="info-label">自己PR：</span><span>{_esc(basic.get("self_pr",""))}</span></div>'
        '<h2>主要スキル</h2>'
        f'<div class="skills-tags">{skill_tags}</div>'
        '<h2>職務経歴</h2>'
        f'{career_html if career_html else "<p style=color:#999>データなし</p>"}'
        '<h2>資格</h2>'
        f'<p>{_esc(certs_html)}</p>'
        '<h2>語学力</h2>'
        f'<p>{_esc(langs_html)}</p>'
        '</body></html>'
    )


def _esc(s: object) -> str:
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
