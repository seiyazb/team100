# TalentOS

IT人材派遣会社向け社内Webアプリ

## 起動方法

1. 依存パッケージのインストール

   ```
   pip install -r requirements.txt
   ```

2. 環境変数の設定

   `.env` ファイルを作成し、以下を設定：

   ```
   DIFY_API_KEY=（DifyのAPIキー。未設定の場合はモック動作）
   DIFY_BASE_URL=（DifyのベースURL。例：https://api.dify.ai）
   SECRET_KEY=（セッション暗号化用の任意の文字列）
   ```

3. 起動

   ```
   uvicorn main:app --reload
   ```

4. アクセス

   http://localhost:8000/login

## テスト用アカウント

| ユーザーID | パスワード | ロール |
|-----------|-----------|-------|
| engineer01 | pass123 | エンジニア |
| sales01 | pass123 | 営業 |
| admin01 | admin123 | 管理者 |

## 画面構成

| URL | 画面名 | アクセス可能なロール |
|-----|--------|-------------------|
| /login | ログイン | 全員 |
| /hearing | AIヒアリング | エンジニア・管理者 |
| /skillsheet | スキルシート | エンジニア・営業・管理者 |
| /search | 人材検索 | 営業・管理者 |
| /users | ユーザー管理 | 管理者のみ |
