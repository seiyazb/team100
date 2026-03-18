# team100 — TalentOS

IT人材派遣会社向け社内Webアプリ

AIヒアリング・スキルシート管理・人材検索を一元化した人材業務支援システムです。

---

## 機能一覧

| 機能 | 対象ロール | 概要 |
|------|-----------|------|
| AIヒアリング | engineer / admin | AIがチャット形式でエンジニアから基本情報・職務経歴・スキルを収集 |
| スキルシート管理 | 全ロール | ヒアリング結果の閲覧・編集・PDF出力。AI最適化（案件通過率向上）も対応 |
| 人材検索 | sales / admin | 自然言語クエリでエンジニアをスキル・経歴から横断検索 |
| ユーザー管理 | admin | ユーザーの作成・一覧表示（engineer / sales / admin の3ロール） |

---

## システム構成

```
Dify ワークフロー（AI処理）
  ├── ヒアリングチャット       # 会話形式でデータ収集 → JSON抽出
  ├── 人材検索クエリ解析       # 自然言語 → 構造化検索条件に変換
  └── スキルシート最適化       # 2段階LLMでスキルシートを高品位化

FastAPI バックエンド
  ├── /api/auth               # ログイン・ログアウト（Cookieセッション）
  ├── /api/hearing            # AIヒアリング・スキルシート最適化
  ├── /api/skillsheet         # スキルシートCRUD・PDF出力
  ├── /api/search             # エンジニア検索
  └── /api/users              # ユーザー管理（adminのみ）

SQLite
  └── users / engineers / skill_sheets / experiences / hearing_logs
```

> Dify ↔ FastAPI 間は `X-API-Key` ヘッダーで認証。  
> Dify未設定時は自動的にモック／キーワード検索にフォールバックします。

---

## ロールと権限

| ロール | ヒアリング | スキルシート | 検索 | ユーザー管理 |
|--------|-----------|-------------|------|------------|
| engineer | ○ | ○（自分のみ） | — | — |
| sales | — | ○（閲覧のみ） | ○ | — |
| admin | ○ | ○（全員） | ○ | ○ |

---

## 起動方法

```bash
cd talentos
pip install -r requirements.txt
uvicorn main:app --reload
```

`.env` ファイルを `talentos/` 内に作成してください（詳細は [talentos/README.md](talentos/README.md) を参照）。

http://localhost:8000/login でアクセスできます。

---

## 環境変数（`.env`）

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `SECRET_KEY` | ✅ | セッション署名キー（任意の文字列） |
| `API_KEY` | ✅ | Dify → FastAPI 認証キー |
| `DIFY_BASE_URL` | — | DifyのベースURL（例: `https://api.dify.ai`） |
| `DIFY_HEARING_API_KEY` | — | ヒアリングチャットのAPIキー |
| `DIFY_OPTIMIZE_API_KEY` | — | スキルシート最適化のAPIキー |
| `DIFY_SEARCH_API_KEY` | — | 人材検索クエリ解析のAPIキー |

Dify関連の変数が未設定の場合、各機能はモック／フォールバック動作します。

---

## テスト

```bash
cd talentos
pytest tests/
```

| テストファイル | 対象 |
|--------------|------|
| `test_auth.py` | ログイン・ログアウト・セッション |
| `test_hearing.py` | AIヒアリング・最適化 |
| `test_skillsheet.py` | スキルシートCRUD・PDF |
| `test_search.py` | 人材検索 |
| `test_users.py` | ユーザー管理 |
| `test_ui_routing.py` | ページルーティング・ロール制御 |

---

## 技術スタック

- **Backend**: FastAPI / SQLite / itsdangerous
- **Frontend**: Jinja2 / Vanilla JS / CSS
- **AI**: Dify（Gemini 2.5 Flash Lite）
- **認証**: Cookieセッション（8時間有効） + API Key（Dify向け）
