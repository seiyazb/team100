# team100 — TalentOS

IT人材派遣会社向け社内Webアプリ

## 起動方法

```bash
cd talentos
pip install -r requirements.txt
uvicorn main:app --reload
```

`.env` ファイルを `talentos/` 内に作成してください（詳細は [talentos/README.md](talentos/README.md) を参照）。

http://localhost:8000/login でアクセスできます。

詳しい手順・アカウント情報は [talentos/README.md](talentos/README.md) を参照してください。
