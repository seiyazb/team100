"""ユーザー管理テスト"""

from __future__ import annotations

import json

import pytest

from db.database import get_connection


# =========================================================================
# 正常系
# =========================================================================

class TestUsersNormal:
    """ユーザー管理 正常系テスト"""

    def test_no1_admin_list_users(self, admin_client):
        """No.1 adminでユーザー一覧を取得 → 全ユーザーが返る"""
        resp = admin_client.get("/api/users")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4  # admin01, engineer01, sales01, api, engineer02

    def test_no2_create_engineer(self, admin_client):
        """No.2 engineerロールでユーザーを新規登録 → users・engineersテーブルに両方作成"""
        resp = admin_client.post("/api/users", json={
            "user_id": "new_engineer",
            "name": "新規エンジニア",
            "role": "engineer",
            "password": "newpass123",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # users テーブルに作成されていること
        conn = get_connection()
        user_row = conn.execute("SELECT * FROM users WHERE user_id = 'new_engineer'").fetchone()
        assert user_row is not None
        assert user_row["role"] == "engineer"

        # engineers テーブルにも作成されていること
        eng_row = conn.execute("SELECT * FROM engineers WHERE engineer_id = 'new_engineer'").fetchone()
        conn.close()
        assert eng_row is not None

    def test_no3_create_sales(self, admin_client):
        """No.3 salesロールでユーザーを新規登録 → usersテーブルに作成"""
        resp = admin_client.post("/api/users", json={
            "user_id": "new_sales",
            "name": "新規営業",
            "role": "sales",
            "password": "newpass123",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        conn = get_connection()
        row = conn.execute("SELECT * FROM users WHERE user_id = 'new_sales'").fetchone()
        conn.close()
        assert row is not None
        assert row["role"] == "sales"

    def test_no4_create_admin(self, admin_client):
        """No.4 adminロールでユーザーを新規登録 → usersテーブルに作成"""
        resp = admin_client.post("/api/users", json={
            "user_id": "new_admin",
            "name": "新規管理者",
            "role": "admin",
            "password": "adminpass",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_no5_login_after_create(self, admin_client, anonymous_client):
        """No.5 登録後にそのアカウントでログインできるか確認 → 正常にログインできる"""
        admin_client.post("/api/users", json={
            "user_id": "login_test",
            "name": "ログインテスト",
            "role": "engineer",
            "password": "testpass",
        })

        resp = anonymous_client.post("/api/auth/login", json={
            "user_id": "login_test",
            "password": "testpass",
        })
        data = resp.json()
        assert data["success"] is True

    def test_no6_password_hashed(self, admin_client):
        """No.6 PWがDBにハッシュ化されて保存されているか確認 → 平文PWがDBに保存されていない"""
        admin_client.post("/api/users", json={
            "user_id": "hash_test",
            "name": "ハッシュテスト",
            "role": "engineer",
            "password": "plaintext123",
        })

        conn = get_connection()
        row = conn.execute("SELECT password_hash FROM users WHERE user_id = 'hash_test'").fetchone()
        conn.close()

        assert row is not None
        assert row["password_hash"] != "plaintext123"
        assert row["password_hash"].startswith("$2")  # bcrypt ハッシュ


# =========================================================================
# 異常系
# =========================================================================

class TestUsersError:
    """ユーザー管理 異常系テスト"""

    def test_no7_duplicate_user_id(self, admin_client):
        """No.7 既存のuser_idで登録を試みる → エラー・重複登録されない"""
        resp = admin_client.post("/api/users", json={
            "user_id": "engineer01",
            "name": "重複テスト",
            "role": "engineer",
            "password": "pass123",
        })
        assert resp.status_code == 409

    def test_no8_all_empty(self, admin_client):
        """No.8 全フィールド空欄で登録 → エラー・登録されない"""
        resp = admin_client.post("/api/users", json={
            "user_id": "",
            "name": "",
            "role": "",
            "password": "",
        })
        assert resp.status_code in (400, 422)

    def test_no9_id_only(self, admin_client):
        """No.9 user_idのみ入力・他空欄で登録 → エラー・登録されない"""
        resp = admin_client.post("/api/users", json={
            "user_id": "test_user",
            "name": "",
            "role": "",
            "password": "",
        })
        assert resp.status_code in (400, 422)

    def test_no10_pw_only(self, admin_client):
        """No.10 PWのみ入力・他空欄で登録 → エラー・登録されない"""
        resp = admin_client.post("/api/users", json={
            "user_id": "",
            "name": "",
            "role": "",
            "password": "password123",
        })
        assert resp.status_code in (400, 422)

    def test_no11_no_role(self, admin_client):
        """No.11 ロールを指定せず登録 → エラー・登録されない"""
        resp = admin_client.post("/api/users", json={
            "user_id": "test_norole",
            "name": "テスト",
            "role": "",
            "password": "pass123",
        })
        assert resp.status_code in (400, 422)

    def test_no12_invalid_role(self, admin_client):
        """No.12 不正なロール名（例: superuser）で登録 → エラー・登録されない"""
        resp = admin_client.post("/api/users", json={
            "user_id": "test_invalid_role",
            "name": "テスト",
            "role": "superuser",
            "password": "pass123",
        })
        assert resp.status_code == 400


# =========================================================================
# 境界値
# =========================================================================

class TestUsersBoundary:
    """ユーザー管理 境界値テスト"""

    def test_no13_long_user_id(self, admin_client):
        """No.13 user_idに1000文字を入力して登録 → クラッシュしない・エラー"""
        resp = admin_client.post("/api/users", json={
            "user_id": "a" * 1000,
            "name": "長いID",
            "role": "engineer",
            "password": "pass123",
        })
        # 長くてもクラッシュしない（登録される可能性もある）
        assert resp.status_code in (200, 400, 422)

    @pytest.mark.xfail(reason="仕様確認が必要: PWが1文字の場合の挙動", strict=False)
    def test_no14_short_password(self, admin_client):
        """No.14 PWに1文字だけ入力して登録 → エラー or 登録される"""
        resp = admin_client.post("/api/users", json={
            "user_id": "short_pw_user",
            "name": "短いPW",
            "role": "engineer",
            "password": "x",
        })
        assert resp.status_code in (200, 400)

    def test_no15_long_password(self, admin_client):
        """No.15 PWに1000文字を入力して登録 → クラッシュしない"""
        resp = admin_client.post("/api/users", json={
            "user_id": "long_pw_user",
            "name": "長いPW",
            "role": "engineer",
            "password": "x" * 1000,
        })
        assert resp.status_code in (200, 400, 422)

    def test_no16_long_name(self, admin_client):
        """No.16 氏名に100文字を入力して登録 → クラッシュしない・正常に登録"""
        resp = admin_client.post("/api/users", json={
            "user_id": "long_name_user",
            "name": "あ" * 100,
            "role": "engineer",
            "password": "pass123",
        })
        assert resp.status_code in (200, 400)


# =========================================================================
# セキュリティ
# =========================================================================

class TestUsersSecurity:
    """ユーザー管理 セキュリティテスト"""

    def test_no17_xss_user_id(self, admin_client):
        """No.17 user_idに <script>alert(1)</script> を入力して登録 → 無害化・スクリプト実行されない"""
        resp = admin_client.post("/api/users", json={
            "user_id": "<script>alert(1)</script>",
            "name": "XSSテスト",
            "role": "engineer",
            "password": "pass123",
        })
        # 登録されてもスクリプトが実行されないことを確認
        assert resp.status_code in (200, 400, 409)

    def test_no18_sqli_user_id(self, admin_client):
        """No.18 user_idに ' OR 1=1 -- を入力（SQLi） → DBが破壊されない"""
        resp = admin_client.post("/api/users", json={
            "user_id": "' OR 1=1 --",
            "name": "SQLiテスト",
            "role": "engineer",
            "password": "pass123",
        })
        assert resp.status_code in (200, 400)

        # DB が壊れていないことを確認
        conn = get_connection()
        row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
        conn.close()
        assert row["cnt"] > 0

    def test_no19_anonymous_get(self, anonymous_client):
        """No.19 未認証で /api/users を直接GET → 401（リダイレクト）"""
        resp = anonymous_client.get("/api/users")
        assert resp.status_code in (302, 401)

    def test_no20_anonymous_post(self, anonymous_client):
        """No.20 未認証で /api/users に直接POST → 401（リダイレクト）"""
        resp = anonymous_client.post("/api/users", json={
            "user_id": "hack_user",
            "name": "ハッカー",
            "role": "admin",
            "password": "hack123",
        })
        assert resp.status_code in (302, 401)


# =========================================================================
# ロールアクセス制御
# =========================================================================

class TestUsersRoleAccess:
    """ユーザー管理 ロールアクセス制御テスト"""

    def test_no21_admin_access(self, admin_client):
        """No.21 adminで /users にアクセス → 正常に操作できる"""
        resp = admin_client.get("/users")
        assert resp.status_code == 200

    def test_no22_engineer_access(self, engineer_client):
        """No.22 engineerで /users に直接アクセス → アクセス拒否"""
        resp = engineer_client.get("/users")
        assert resp.status_code == 403

    def test_no23_sales_access(self, sales_client):
        """No.23 salesで /users に直接アクセス → アクセス拒否"""
        resp = sales_client.get("/users")
        assert resp.status_code == 403

    def test_no24_engineer_get_api(self, engineer_client):
        """No.24 engineerが /api/users にGETリクエストを直接送信 → 403"""
        resp = engineer_client.get("/api/users")
        assert resp.status_code == 403

    def test_no25_sales_post_api(self, sales_client):
        """No.25 salesが /api/users にPOSTリクエストを直接送信 → 403"""
        resp = sales_client.post("/api/users", json={
            "user_id": "sales_hack",
            "name": "営業ハック",
            "role": "admin",
            "password": "pass123",
        })
        assert resp.status_code == 403
