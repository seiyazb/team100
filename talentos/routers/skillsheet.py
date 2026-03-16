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
            # tool_info → tools に正規化（Dify側のキー名揺れ対応）
            if "tool_info" in skills_data and "tools" not in skills_data:
                skills_data["tools"] = skills_data["tool_info"]
        if opt:
            optimized[s["theme"]] = opt

    career_list: list[dict] = []
    if career_from_sheet and isinstance(career_from_sheet, dict):
        # experiences 配列がある場合（Dify/モック共通形式）
        if isinstance(career_from_sheet.get("experiences"), list):
            for exp in career_from_sheet["experiences"]:
                if isinstance(exp, dict) and exp.get("project_name"):
                    career_list.append(exp)
        # 直接 project_name がある場合（フォールバック）
        elif career_from_sheet.get("project_name"):
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

    # --- 技術スキル集計 ---
    all_skills: list[str] = []
    for c in career_list:
        all_skills.extend(c.get("tech_stack", []))
    all_skills.extend(skills.get("tools", []) or skills.get("tool_info", []))
    unique_skills: list[str] = list(dict.fromkeys(all_skills))

    # --- 資格 ---
    certs: list = skills.get("certifications", [])
    certs_html: str = "、".join(_esc(c) for c in certs) if certs else "―"

    # --- 語学 ---
    langs: list = skills.get("language_skills", [])
    langs_rows: str = ""
    for lg in langs:
        langs_rows += f'<tr><td>{_esc(lg.get("language",""))}</td><td>{_esc(lg.get("level",""))}</td></tr>'

    # --- 基本情報テーブル ---
    school: str = " ".join(filter(None, [basic.get("school_name",""), basic.get("faculty_name",""), basic.get("department_name","")]))
    relocation: str = "可" if basic.get("relocation_ok") else "不可" if basic.get("relocation_ok") is not None else "―"

    # --- 職務経歴テーブル ---
    career_rows: str = ""
    for i, c in enumerate(career_list, 1):
        ts = c.get("tech_stack", [])
        # 技術をカテゴリ分けせず一覧表示
        tech_str: str = "、".join(_esc(t) for t in ts) if ts else "―"
        period: str = f'{_esc(c.get("period_start",""))} ～ {_esc(c.get("period_end","現在"))}'
        team: str = f'{c.get("team_size","―")}名' if c.get("team_size") else "―"
        career_rows += (
            f'<tr>'
            f'<td class="no">{i}</td>'
            f'<td class="period">{period}</td>'
            f'<td class="detail">'
            f'<div class="project-name">【{_esc(c.get("project_name",""))}】</div>'
            f'<div class="career-meta">'
            f'<span>役割：{_esc(c.get("role_title","―"))}</span>'
            f'<span class="sep">／</span>'
            f'<span>規模：{team}</span>'
            f'</div>'
            f'<div class="desc">{_esc(c.get("description",""))}</div>'
            f'<div class="tech-row"><span class="tech-label">使用技術：</span>{tech_str}</div>'
            f'</td>'
            f'</tr>'
        )

    if not career_rows:
        career_rows = '<tr><td colspan="3" style="text-align:center;color:#999;padding:20px;">職務経歴データなし</td></tr>'

    # --- 技術スキルサマリ行 ---
    skill_cells: str = ""
    for s in unique_skills:
        skill_cells += f'<span class="skill-chip">{_esc(s)}</span>'

    return (
        '<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">'
        '<style>'
        '@page { size: A4; margin: 15mm 12mm; }'
        'body { font-family: "Noto Sans JP", "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif;'
        '  margin: 0; padding: 0; color: #222; font-size: 10pt; line-height: 1.6; }'
        'h1 { text-align: center; font-size: 16pt; margin: 0 0 6px; padding: 10px 0 8px;'
        '  border-bottom: 3px double #333; letter-spacing: 4px; }'
        '.subtitle { text-align: right; font-size: 9pt; color: #666; margin-bottom: 14px; }'
        'table { width: 100%; border-collapse: collapse; margin-bottom: 14px; }'
        'th, td { border: 1px solid #999; padding: 5px 8px; vertical-align: top; font-size: 9.5pt; }'
        'th { background: #f0f0f0; font-weight: 600; white-space: nowrap; text-align: center; width: 100px; }'
        '.section-header { background: #2c3e50; color: #fff; font-size: 11pt; font-weight: 600;'
        '  padding: 6px 10px; letter-spacing: 2px; margin-top: 10px; margin-bottom: 0; }'
        '.section-header + table { margin-top: 0; }'
        '.career-table th { background: #f0f0f0; }'
        '.career-table .no { width: 30px; text-align: center; }'
        '.career-table .period { width: 110px; text-align: center; font-size: 9pt; white-space: nowrap; }'
        '.career-table .detail { text-align: left; }'
        '.project-name { font-weight: 700; font-size: 10pt; margin-bottom: 3px; }'
        '.career-meta { font-size: 9pt; color: #555; margin-bottom: 4px; }'
        '.career-meta .sep { margin: 0 4px; }'
        '.desc { font-size: 9pt; margin-bottom: 4px; line-height: 1.5; }'
        '.tech-row { font-size: 8.5pt; color: #444; }'
        '.tech-label { font-weight: 600; }'
        '.skill-chip { display: inline-block; background: #e8f4fd; border: 1px solid #b3d9f2;'
        '  border-radius: 3px; padding: 1px 8px; margin: 2px 3px; font-size: 8.5pt; }'
        '.pr-box { border: 1px solid #999; padding: 8px 10px; font-size: 9.5pt; line-height: 1.7;'
        '  min-height: 40px; margin-bottom: 14px; }'
        '.lang-table { width: auto; min-width: 300px; }'
        '.lang-table th { width: 120px; }'
        '</style></head><body>'

        # ===== ヘッダー =====
        '<h1>スキルシート</h1>'

        # ===== 基本情報 =====
        '<div class="section-header">基本情報</div>'
        '<table>'
        f'<tr><th>氏名</th><td colspan="3">{_esc(data.get("name",""))}</td></tr>'
        f'<tr><th>専門分野</th><td>{_esc(data.get("specialty",""))}</td>'
        f'<th>スキルレベル</th><td>{_esc(basic.get("skill_level",""))}</td></tr>'
        f'<tr><th>最終学歴</th><td colspan="3">{_esc(school)}</td></tr>'
        f'<tr><th>勤務地</th><td>{_esc(basic.get("work_location",""))}</td>'
        f'<th>最寄駅</th><td>{_esc(basic.get("nearest_station",""))}</td></tr>'
        f'<tr><th>転勤</th><td>{relocation}</td>'
        f'<th>趣味・特技</th><td>{_esc(basic.get("hobbies",""))}</td></tr>'
        '</table>'

        # ===== 資格 =====
        '<div class="section-header">保有資格</div>'
        '<table>'
        f'<tr><td>{certs_html}</td></tr>'
        '</table>'

        # ===== 語学力 =====
        '<div class="section-header">語学力</div>'
        f'<table class="lang-table">'
        f'<tr><th>言語</th><th>レベル</th></tr>'
        f'{langs_rows if langs_rows else "<tr><td colspan=2>―</td></tr>"}'
        f'</table>'

        # ===== 技術スキルサマリ =====
        '<div class="section-header">技術スキル</div>'
        '<div style="border:1px solid #999;border-top:none;padding:8px 10px;margin-bottom:14px;">'
        f'{skill_cells if skill_cells else "―"}'
        '</div>'

        # ===== 自己PR =====
        '<div class="section-header">自己PR</div>'
        f'<div class="pr-box">{_esc(basic.get("self_pr",""))}</div>'

        # ===== 職務経歴 =====
        '<div class="section-header">職務経歴</div>'
        '<table class="career-table">'
        '<tr><th class="no">No.</th><th class="period">期間</th><th class="detail">業務内容</th></tr>'
        f'{career_rows}'
        '</table>'

        '</body></html>'
    )


def _esc(s: object) -> str:
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
