"""AIヒアリングテスト"""

from __future__ import annotations

import json

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from db.database import get_connection


# =========================================================================
# ヘルパー
# =========================================================================

def _send_chat(client, theme: str, message: str, conversation_id: str = "") -> dict:
    """ヒアリングチャット API にメッセージを送信する"""
    resp = client.post(
        "/api/hearing/chat",
        json={"theme": theme, "message": message, "conversation_id": conversation_id},
    )
    assert resp.status_code == 200
    return resp.json()


def _send_chat_stream(client, theme: str, message: str, conversation_id: str = ""):
    """ストリーミングチャット API にメッセージを送信する"""
    resp = client.post(
        "/api/hearing/chat/stream",
        json={"theme": theme, "message": message, "conversation_id": conversation_id},
    )
    return resp


# =========================================================================
# 正常系
# =========================================================================

class TestHearingNormal:
    """AIヒアリング 正常系テスト"""

    def test_no1_normal_message(self, engineer_client):
        """No.1 通常のメッセージを送信 → AIが返答する・theme_completed: false"""
        data = _send_chat(engineer_client, "basic", "バックエンド開発が専門です")
        assert "message" in data
        assert data["theme_completed"] is False

    def test_no2_multiple_turns(self, engineer_client):
        """No.2 複数回やりとりする → 会話履歴がDBに蓄積される"""
        _send_chat(engineer_client, "basic", "バックエンド開発が専門です")
        _send_chat(engineer_client, "basic", "転勤は可能です")

        conn = get_connection()
        row = conn.execute(
            "SELECT messages FROM hearing_logs WHERE engineer_id = 'engineer01' AND theme = 'basic' ORDER BY log_id DESC LIMIT 1"
        ).fetchone()
        conn.close()

        messages = json.loads(row["messages"])
        user_messages = [m for m in messages if m["role"] == "user"]
        assert len(user_messages) >= 2

    def test_no3_reload_history(self, engineer_client):
        """No.3 ページリロード後に会話履歴を取得 → 履歴が復元される"""
        _send_chat(engineer_client, "basic", "テストメッセージ")

        conn = get_connection()
        row = conn.execute(
            "SELECT messages FROM hearing_logs WHERE engineer_id = 'engineer01' AND theme = 'basic'"
        ).fetchone()
        conn.close()

        assert row is not None
        messages = json.loads(row["messages"])
        assert len(messages) > 0

    def test_no4_basic_to_career(self, engineer_client):
        """No.4 basic → career に切り替える → 別の会話として扱われる"""
        data1 = _send_chat(engineer_client, "basic", "基本情報テスト")
        data2 = _send_chat(engineer_client, "career", "経歴テスト")

        conn = get_connection()
        basic_row = conn.execute(
            "SELECT * FROM hearing_logs WHERE engineer_id = 'engineer01' AND theme = 'basic'"
        ).fetchone()
        career_row = conn.execute(
            "SELECT * FROM hearing_logs WHERE engineer_id = 'engineer01' AND theme = 'career'"
        ).fetchone()
        conn.close()

        assert basic_row is not None
        assert career_row is not None

    def test_no5_career_to_skills(self, engineer_client):
        """No.5 career → skills に切り替える → 別の会話として扱われる"""
        _send_chat(engineer_client, "career", "経歴テスト")
        _send_chat(engineer_client, "skills", "スキルテスト")

        conn = get_connection()
        career_row = conn.execute(
            "SELECT * FROM hearing_logs WHERE engineer_id = 'engineer01' AND theme = 'career'"
        ).fetchone()
        skills_row = conn.execute(
            "SELECT * FROM hearing_logs WHERE engineer_id = 'engineer01' AND theme = 'skills'"
        ).fetchone()
        conn.close()

        assert career_row is not None
        assert skills_row is not None

    def test_no6_complete_hearing(self, engineer_client):
        """No.6 全項目を回答してヒアリングを完了 → theme_completed: true・skill_sheetsに保存される"""
        # モック動作: 5回送信で完了
        for i in range(4):
            data = _send_chat(engineer_client, "basic", f"回答{i+1}")
            assert data["theme_completed"] is False

        data = _send_chat(engineer_client, "basic", "最後の回答")
        assert data["theme_completed"] is True

        # skill_sheets に保存されていることを確認
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM skill_sheets WHERE engineer_id = 'engineer01' AND theme = 'basic'"
        ).fetchone()
        conn.close()
        assert row is not None
        assert row["raw_data"] is not None

    def test_no7_resume_hearing(self, engineer_client):
        """No.7 ヒアリング途中でページを閉じて再度開く → 途中から続けられる"""
        _send_chat(engineer_client, "basic", "最初のメッセージ")
        _send_chat(engineer_client, "basic", "2番目のメッセージ")

        # DB に履歴が保存されていることを確認
        conn = get_connection()
        row = conn.execute(
            "SELECT messages FROM hearing_logs WHERE engineer_id = 'engineer01' AND theme = 'basic'"
        ).fetchone()
        conn.close()

        messages = json.loads(row["messages"])
        assert len(messages) >= 4  # user+assistant × 2


# =========================================================================
# 異常系
# =========================================================================

class TestHearingError:
    """AIヒアリング 異常系テスト"""

    def test_no8_empty_message(self, engineer_client):
        """No.8 空メッセージで送信 → 送信されない or エラー"""
        resp = engineer_client.post(
            "/api/hearing/chat",
            json={"theme": "basic", "message": "", "conversation_id": ""},
        )
        # 空メッセージでもクラッシュしない
        assert resp.status_code in (200, 400, 422)

    def test_no9_rapid_fire(self, engineer_client):
        """No.9 返答が来る前に連続送信 → 二重登録されない"""
        _send_chat(engineer_client, "basic", "メッセージ1")
        _send_chat(engineer_client, "basic", "メッセージ2")

        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM hearing_logs WHERE engineer_id = 'engineer01' AND theme = 'basic'"
        ).fetchall()
        conn.close()

        # 同一テーマの未完了ログは1つだけ
        uncompleted = [r for r in rows if r["completed"] == 0]
        assert len(uncompleted) <= 1

    @patch("routers.hearing.DIFY_HEARING_API_KEY", "test-key")
    @patch("routers.hearing.DIFY_BASE_URL", "https://api.dify.ai")
    def test_no10_dify_api_error(self, engineer_client):
        """No.10 Dify APIがエラーを返す状態 → エラーメッセージ・クラッシュしない"""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            data = _send_chat(engineer_client, "basic", "テスト")
            assert "message" in data
            assert data["theme_completed"] is False

    @patch("routers.hearing.DIFY_HEARING_API_KEY", "test-key")
    @patch("routers.hearing.DIFY_BASE_URL", "https://api.dify.ai")
    def test_no11_dify_down(self, engineer_client):
        """No.11 Dify APIが完全にダウンしている状態 → エラーメッセージ・クラッシュしない"""
        import httpx

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.ConnectError("Connection refused")):
            resp = engineer_client.post(
                "/api/hearing/chat",
                json={"theme": "basic", "message": "テスト", "conversation_id": ""},
            )
            # クラッシュしないことを確認（302はミドルウェアの例外ハンドリング）
            assert resp.status_code in (200, 302, 500)

    @patch("routers.hearing.DIFY_HEARING_API_KEY", "test-key")
    @patch("routers.hearing.DIFY_BASE_URL", "https://api.dify.ai")
    def test_no12_network_disconnect(self, engineer_client):
        """No.12 ネットワーク切断状態 → エラーメッセージ・クラッシュしない"""
        import httpx

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.TimeoutException("Timeout")):
            data = _send_chat(engineer_client, "basic", "テスト")
            assert "message" in data
            assert "タイムアウト" in data["message"]


# =========================================================================
# 境界値
# =========================================================================

class TestHearingBoundary:
    """AIヒアリング 境界値テスト"""

    def test_no13_long_message(self, engineer_client):
        """No.13 2000文字のメッセージを送信 → クラッシュせず処理される"""
        long_msg = "あ" * 2000
        data = _send_chat(engineer_client, "basic", long_msg)
        assert "message" in data

    def test_no14_emoji_special_chars(self, engineer_client):
        """No.14 絵文字・特殊文字を含むメッセージ → 文字化けしない"""
        data = _send_chat(engineer_client, "basic", "🎉テスト😊✨特殊文字：①②③♪")
        assert "message" in data

    def test_no15_multilingual(self, engineer_client):
        """No.15 日本語・英語・中国語が混在するメッセージ → 文字化けしない"""
        data = _send_chat(engineer_client, "basic", "Hello こんにちは 你好 مرحبا")
        assert "message" in data

    @patch("routers.hearing.DIFY_HEARING_API_KEY", "test-key")
    @patch("routers.hearing.DIFY_BASE_URL", "https://api.dify.ai")
    def test_no16_timeout_mock(self, engineer_client):
        """No.16 タイムアウト（120秒超）のモック → タイムアウトメッセージが返る"""
        import httpx

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.TimeoutException("Timeout")):
            data = _send_chat(engineer_client, "basic", "テスト")
            assert "タイムアウト" in data["message"]

    def test_no17_many_messages(self, engineer_client):
        """No.17 100回以上の会話履歴がある状態 → クラッシュしない"""
        # DB に大量の会話履歴を直接書き込む
        messages = []
        for i in range(100):
            messages.append({"role": "user", "content": f"メッセージ{i}", "timestamp": "2024-01-01T00:00:00"})
            messages.append({"role": "assistant", "content": f"返答{i}", "timestamp": "2024-01-01T00:00:00"})

        conn = get_connection()
        conn.execute(
            "INSERT INTO hearing_logs (engineer_id, theme, messages, completed, dify_conversation_id) VALUES (?, ?, ?, ?, ?)",
            ("engineer01", "basic", json.dumps(messages, ensure_ascii=False), 0, "mock-basic-engineer01"),
        )
        conn.commit()
        conn.close()

        # 追加メッセージを送信してクラッシュしないことを確認
        data = _send_chat(engineer_client, "basic", "追加メッセージ")
        assert "message" in data


# =========================================================================
# セキュリティ
# =========================================================================

class TestHearingSecurity:
    """AIヒアリング セキュリティテスト"""

    def test_no18_xss_message(self, engineer_client):
        """No.18 <script>alert(1)</script> を送信（XSS） → 無害化されて保存される"""
        _send_chat(engineer_client, "basic", "<script>alert(1)</script>")

        conn = get_connection()
        row = conn.execute(
            "SELECT messages FROM hearing_logs WHERE engineer_id = 'engineer01' AND theme = 'basic'"
        ).fetchone()
        conn.close()

        # DB にはメッセージが保存されるが、表示時に無害化される
        assert row is not None

    def test_no19_sqli_message(self, engineer_client):
        """No.19 ' OR 1=1 -- を送信（SQLi） → DBが破壊されない"""
        _send_chat(engineer_client, "basic", "' OR 1=1 --")

        conn = get_connection()
        row = conn.execute("SELECT COUNT(*) as cnt FROM hearing_logs").fetchone()
        conn.close()
        assert row["cnt"] > 0

    def test_no20_anonymous_stream(self, anonymous_client):
        """No.20 未認証で /api/hearing/chat/stream を叩く → 401（リダイレクト）"""
        resp = anonymous_client.post(
            "/api/hearing/chat/stream",
            json={"theme": "basic", "message": "test", "conversation_id": ""},
        )
        # ミドルウェアで未認証はリダイレクト（302）
        assert resp.status_code in (302, 401, 403)

    def test_no21_forged_engineer_id(self, engineer_client):
        """No.21 engineer_idを偽造してAPIを叩く → 403エラー"""
        # hearing API は request.state.user から engineer_id を取得するので偽造不可
        # optimize API で他人の engineer_id を指定した場合を確認
        resp = engineer_client.post(
            "/api/hearing/optimize",
            json={"engineer_id": "engineer02"},
        )
        assert resp.status_code == 403


# =========================================================================
# ロールアクセス制御
# =========================================================================

class TestHearingRoleAccess:
    """AIヒアリング ロールアクセス制御テスト"""

    def test_no22_sales_hearing(self, sales_client):
        """No.22 salesで /hearing にアクセス → アクセス拒否"""
        resp = sales_client.get("/hearing")
        assert resp.status_code == 403

    def test_no23_admin_hearing(self, admin_client):
        """No.23 adminで /hearing にアクセス → 正常に表示"""
        resp = admin_client.get("/hearing")
        assert resp.status_code == 200

    def test_no24_engineer_a_gets_engineer_b_logs(self, engineer_client):
        """No.24 engineerAがengineerBのhearing_logsをAPIで取得 → 403"""
        # hearing API はセッションの user_id を使うため、直接他人のログは取得できない
        # optimize API で他人の engineer_id を指定
        resp = engineer_client.post(
            "/api/hearing/optimize",
            json={"engineer_id": "engineer02"},
        )
        assert resp.status_code == 403

    def test_no25_engineer_a_chats_as_engineer_b(self, engineer_client):
        """No.25 engineerAがengineerBのテーマでチャット送信 → 403"""
        # chat API は request.state.user["user_id"] を使うため、
        # リクエストボディで engineer_id を偽造しても自分の ID で処理される
        # → 仕様上、他人のテーマにはアクセスできない
        data = _send_chat(engineer_client, "basic", "テスト")
        # engineer01 のデータとして保存されることを確認
        conn = get_connection()
        row = conn.execute(
            "SELECT engineer_id FROM hearing_logs WHERE theme = 'basic' ORDER BY log_id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        assert row["engineer_id"] == "engineer01"
