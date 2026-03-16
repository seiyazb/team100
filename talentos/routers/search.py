"""人材検索（Dify連携 / モック対応）"""

from __future__ import annotations

import json
import logging
import os
import re
from fastapi import APIRouter, Request
from pydantic import BaseModel

from db.database import get_connection

logger = logging.getLogger("search")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s] %(message)s"))
    logger.addHandler(_handler)

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
    if not keywords:
        return []

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
    logger.info("[do_search] query=%s, use_dify=%s", query, _use_dify())

    if _use_dify():
        return await _dify_search(query, request)

    keywords: list[str] = _extract_keywords(query)
    logger.info("[do_search] keywords=%s", keywords)
    results: list[dict] = _search_engineers(keywords)
    logger.info("[do_search] results count=%d", len(results))
    if not keywords:
        ai_insight = "技術キーワードが検出できませんでした。技術名（例: Python, AWS, React）を含めて検索してください。"
    else:
        kw_text: str = "・".join(keywords)
        ai_insight = (
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

    logger.info("[Dify request] query=%s, payload=%s", query, json.dumps(payload, ensure_ascii=False))

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                DIFY_BASE_URL + "/v1/workflows/run", json=payload, headers=headers
            )

        logger.info("[Dify response] status=%s", resp.status_code)
        logger.info("[Dify response] body=%s", resp.text)

        if resp.status_code != 200:
            logger.warning("[Dify fallback] status=%s, falling back to keyword search", resp.status_code)
            keywords: list[str] = _extract_keywords(query)
            results: list[dict] = _search_engineers(keywords)
            return {
                "ai_insight": "AI機能が一時的に利用できません。キーワード検索で代替しました。",
                "results": results,
            }

        data: dict = resp.json()
        outputs: dict = data.get("data", {}).get("outputs", {})
        result_raw = outputs.get("result", "{}")
        logger.info("[Dify parse] outputs=%s", json.dumps(outputs, ensure_ascii=False))
        logger.info("[Dify parse] result_raw type=%s, value=%s", type(result_raw).__name__, result_raw)

        try:
            parsed: dict = json.loads(result_raw) if isinstance(result_raw, str) else result_raw if isinstance(result_raw, dict) else {}
        except (json.JSONDecodeError, TypeError):
            parsed = {}
        logger.info("[Dify parse] parsed=%s", json.dumps(parsed, ensure_ascii=False) if isinstance(parsed, dict) else str(parsed))

        ai_insight: str = parsed.get("ai_insight", "検索結果です。")
        # skills はトップレベルまたは conditions 内のどちらにも対応
        raw_skills = parsed.get("skills", []) or parsed.get("conditions", {}).get("skills", [])
        logger.info("[Dify parse] raw_skills=%s", raw_skills)
        # Dify returns skills as [{"name": "Python", ...}, ...] — extract names
        keywords = [
            s["name"] if isinstance(s, dict) and "name" in s else str(s)
            for s in raw_skills
        ]
        logger.info("[Dify search] keywords=%s", keywords)
        results = _search_engineers(keywords)
        logger.info("[Dify search] results count=%d", len(results))
        return {
            "ai_insight": ai_insight,
            "search_summary": parsed.get("search_summary", ""),
            "results": results,
        }
    except httpx.TimeoutException:
        logger.warning("[Dify error] timeout")
        keywords = _extract_keywords(query)
        results = _search_engineers(keywords)
        return {
            "ai_insight": "AIの応答がタイムアウトしました。キーワード検索で代替しました。",
            "results": results,
        }
    except Exception as exc:
        logger.exception("[Dify error] unexpected: %s", exc)
        keywords = _extract_keywords(query)
        results = _search_engineers(keywords)
        return {
            "ai_insight": "検索結果です（" + str(len(results)) + "件）。",
            "results": results,
        }
