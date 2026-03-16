"""SQLite 接続・初期化"""

from __future__ import annotations

import sqlite3
import os
from passlib.hash import bcrypt
from db.models import TABLES

DB_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "talentos.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    for sql in TABLES:
        cur.execute(sql)

    # 初期ユーザー
    seed_users: list[tuple[str, str, str, str]] = [
        ("admin01", "admin123", "管理者", "admin"),
        ("engineer01", "pass123", "山田 太郎", "engineer"),
        ("sales01", "pass123", "佐藤 花子", "sales"),
        ("api", "api-no-login", "API", "admin"),
    ]
    for user_id, password, name, role in seed_users:
        cur.execute(
            "INSERT OR IGNORE INTO users (user_id, password_hash, name, role) VALUES (?, ?, ?, ?)",
            (user_id, bcrypt.hash(password), name, role),
        )

    # engineer01 の engineers レコードも作成（既存コードとの互換性）
    cur.execute(
        "INSERT OR IGNORE INTO engineers (engineer_id, specialty) VALUES (?, ?)",
        ("engineer01", ""),
    )

    conn.commit()
    conn.close()

    # テスト用エンジニア30名を投入
    from db.seed_data import insert_seed_engineers
    insert_seed_engineers()
