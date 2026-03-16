"""人材検索（Dify連携 / モック対応）"""

from __future__ import annotations

import json
import os
import re
from fastapi import APIRouter, Request
from pydantic import BaseModel

from db.database import get_connection

router = APIRouter(prefix="/api/search", tags=["search"])

DIFY_BASE_URL: str = os.getenv("DIFY_BASE_URL", "")
DIFY_SEARCH_API_KEY: str = os.getenv("DIFY_SEARCH_API_KEY", "")


class SearchRequest(BaseModel):
    query: str


def _use_dify() -> bool:
    return bool(DIFY_SEARCH_API_KEY and DIFY_BASE_URL)


def _extract_keywords(query: str) -> list[str]:
    known: list[str] = [
        "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C#", "PHP", "Ruby", "Swift",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Linux",
        "React", "Vue", "Angular", "Next.js", "Node.js", "FastAPI", "Django", "Flask", "Spring",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite",
        "GitHub", "GitHub Actions", "CI/CD", "Git",
    ]
    found: list[str] = []
    q_upper: str = query.upper()
    for k in known:
        if k.upper() in q_upper:
            found.append(k)
    if not found:
        words: list[str] = re.findall(r'[A-Za-z#.+]+', query)
        found = [w for w in words if len(w) >= 2]
    return found


def _search_engineers(keywords: list[str]) -> list[dict]:
    conn = get_connection()
    engineers = conn.execute(
        "SELECT u.user_id, u.name, e.specialty "
        "FROM users u LEFT JOIN engineers e ON u.user_id = e.engineer_id "
        "WHERE u.role = 'engineer'"
    ).fetchall()

    results: list[dict] = []
    for eng in engineers:
        eid: str = eng["user_id"]
        sheets = conn.execute(
            "SELECT theme, raw_data FROM skill_sheets WHERE engineer_id = ?", (eid,)
        ).fetchall()

        all_skills: list[str] = []
        latest_role: str = ""
        exp_summary: str = ""
        for s in sheets:
            raw: dict = json.loads(s["raw_data"]) if s["raw_data"] else {}
            if s["theme"] == "career":
                # experiences 配列内のネストデータを展開
                career_entries: list[dict] = []
                if isinstance(raw.get("experiences"), list):
                    career_entries = raw["experiences"]
                elif raw.get("project_name"):
                    career_entries = [raw]

                for entry in career_entries:
                    ts = entry.get("tech_stack", [])
                    if isinstance(ts, list):
                        all_skills.extend(ts)
                    if not latest_role:
                        latest_role = entry.get("role_title", "")
                    if not exp_summary:
                        exp_summary = entry.get("description", "")
            elif s["theme"] == "skills":
                for key in ("tools", "tool_info", "certifications"):
                    items = raw.get(key, [])
                    if isinstance(items, list):
                        all_skills.extend(items)

        exps = conn.execute(
            "SELECT role_title, tech_stack, description FROM experiences "
            "WHERE engineer_id = ? ORDER BY period_start DESC LIMIT 1",
            (eid,),
        ).fetchall()
        for e in exps:
            ts = json.loads(e["tech_stack"]) if e["tech_stack"] else []
            all_skills.extend(ts)
            if not latest_role:
                latest_role = e["role_title"] or ""
            if not exp_summary:
                exp_summary = e["description"] or ""

        unique_skills: list[str] = list(dict.fromkeys(all_skills))

        matched: list[str] = []
        for kw in keywords:
            for sk in unique_skills:
                if kw.upper() in sk.upper():
                    matched.append(sk)
                    break

        if keywords and not matched:
            continue

        results.append({
            "engineer_id": eid,
            "name": eng["name"],
            "specialty": eng["specialty"] or "",
            "matched_skills": matched,
            "top_skills": unique_skills[:6],
            "latest_role": latest_role,
            "experience_summary": exp_summary[:100] if exp_summary else "",
        })

    conn.close()
    return results


@router.post("")
async def do_search(body: SearchRequest, request: Request) -> dict:
    query: str = body.query.strip()

    if _use_dify():
        return await _dify_search(query, request)

    keywords: list[str] = _extract_keywords(query)
    results: list[dict] = _search_engineers(keywords)
    kw_text: str = "・".join(keywords) if keywords else query
    ai_insight: str = (
        kw_text + "に関連するエンジニアを検索しました。"
        + str(len(results)) + "件の結果が見つかりました。"
    )
    return {"ai_insight": ai_insight, "results": results}


async def _dify_search(query: str, request: Request) -> dict:
    import httpx

    user: dict = request.state.user
    payload: dict = {
        "inputs": {"search_query": query},
        "response_mode": "blocking",
        "user": user["user_id"],
    }
    headers: dict = {"Authorization": "Bearer " + DIFY_SEARCH_API_KEY}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                DIFY_BASE_URL + "/v1/workflows/run", json=payload, headers=headers
            )

        if resp.status_code >= 500:
            keywords: list[str] = _extract_keywords(query)
            results: list[dict] = _search_engineers(keywords)
            return {
                "ai_insight": "AI機能が一時的に利用できません。キーワード検索で代替しました。",
                "results": results,
            }

        data: dict = resp.json()
        outputs: dict = data.get("data", {}).get("outputs", {})
        result_str: str = outputs.get("result", "{}")
        try:
            parsed: dict = json.loads(result_str)
        except (json.JSONDecodeError, TypeError):
            parsed = {}
        conditions: dict = parsed.get("conditions", {})
        ai_insight: str = parsed.get("ai_insight", "検索結果です。")
        keywords = conditions.get("skills", [])
        results = _search_engineers(keywords)
        return {
            "ai_insight": ai_insight,
            "search_summary": parsed.get("search_summary", ""),
            "results": results,
        }
    except httpx.TimeoutException:
        keywords = _extract_keywords(query)
        results = _search_engineers(keywords)
        return {
            "ai_insight": "AIの応答がタイムアウトしました。キーワード検索で代替しました。",
            "results": results,
        }
    except Exception:
        keywords = _extract_keywords(query)
        results = _search_engineers(keywords)
        return {
            "ai_insight": "検索結果です（" + str(len(results)) + "件）。",
            "results": results,
        }
