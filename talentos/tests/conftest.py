"""共通フィクスチャ・DB初期化"""

from __future__ import annotations

import os
import sys
import tempfile

import pytest

# テスト用環境変数を先にセット（main.py が import 時に SECRET_KEY を参照するため）
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")
os.environ["DIFY_BASE_URL"] = ""
os.environ["DIFY_HEARING_API_KEY"] = ""
os.environ["DIFY_OPTIMIZE_API_KEY"] = ""
os.environ["DIFY_SEARCH_API_KEY"] = ""

# talentos ディレクトリを sys.path に追加
_talentos_dir = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(_talentos_dir))

from passlib.hash import bcrypt
from itsdangerous import URLSafeTimedSerializer
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# テスト用 DB（毎テスト初期化）
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _setup_test_db(tmp_path):
    """各テスト前にテスト専用 SQLite ファイルで DB を初期化する"""
    import db.database as _db_mod

    test_db = str(tmp_path / "test_talentos.db")
    _db_mod.DB_PATH = test_db

    # DB 初期化（テーブル作成 + 初期ユーザー）
    _db_mod.init_db()

    # テスト指示書で要求されている追加ユーザー (engineer02)
    conn = _db_mod.get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, password_hash, name, role) VALUES (?, ?, ?, ?)",
        ("engineer02", bcrypt.hash("pass123"), "鈴木 次郎", "engineer"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO engineers (engineer_id) VALUES (?)",
        ("engineer02",),
    )
    # engineer01 用の engineers レコードも作成
    conn.execute(
        "INSERT OR IGNORE INTO engineers (engineer_id) VALUES (?)",
        ("engineer01",),
    )
    conn.commit()
    conn.close()

    yield

    # 後片付け（ファイルは tmp_path が自動削除）


# ---------------------------------------------------------------------------
# FastAPI TestClient
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """テスト用 FastAPI アプリを返す"""
    from main import app as _app
    return _app


@pytest.fixture()
def anonymous_client(app):
    """未ログインクライアント"""
    return TestClient(app, follow_redirects=False)


def _make_session_cookie(app, user_id: str, name: str, role: str) -> str:
    """セッション Cookie 値を生成する"""
    serializer = URLSafeTimedSerializer(app.state.secret_key)
    token = serializer.dumps({"user_id": user_id, "name": name, "role": role})
    return token


@pytest.fixture()
def engineer_client(app):
    """engineer01 でログイン済みクライアント"""
    client = TestClient(app, follow_redirects=False)
    token = _make_session_cookie(app, "engineer01", "山田 太郎", "engineer")
    client.cookies.set("session", token)
    return client


@pytest.fixture()
def engineer02_client(app):
    """engineer02 でログイン済みクライアント（他ユーザーアクセステスト用）"""
    client = TestClient(app, follow_redirects=False)
    token = _make_session_cookie(app, "engineer02", "鈴木 次郎", "engineer")
    client.cookies.set("session", token)
    return client


@pytest.fixture()
def sales_client(app):
    """sales01 でログイン済みクライアント"""
    client = TestClient(app, follow_redirects=False)
    token = _make_session_cookie(app, "sales01", "佐藤 花子", "sales")
    client.cookies.set("session", token)
    return client


@pytest.fixture()
def admin_client(app):
    """admin01 でログイン済みクライアント"""
    client = TestClient(app, follow_redirects=False)
    token = _make_session_cookie(app, "admin01", "管理者", "admin")
    client.cookies.set("session", token)
    return client
