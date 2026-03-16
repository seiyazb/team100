"""テスト用シードデータ（エンジニア30名分）

init_db() から呼ばれ、初回起動時にのみ INSERT される。
検索テストで絞り込みやすいようスキルスタックを分散させている。
"""

from __future__ import annotations

import json

# fmt: off
SEED_ENGINEERS: list[dict] = [
    # ---- バックエンド系 ----
    {
        "user_id": "eng_tanaka", "password": "pass123", "name": "田中 一郎", "specialty": "バックエンド開発",
        "work_location": "東京都", "nearest_station": "渋谷駅", "relocation_ok": 1,
        "school": "東京大学 工学部 情報工学科", "skill_level": "上級",
        "self_pr": "Python/FastAPIを用いたAPI設計を得意とし、大規模トラフィックにも対応可能なアーキテクチャ設計の経験があります。",
        "hobbies": "ランニング、読書",
        "career": [
            {"project_name": "ECサイトAPI基盤構築", "period_start": "2023/04", "period_end": "2024/03",
             "team_size": 6, "role_title": "テックリード",
             "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
             "description": "マイクロサービスアーキテクチャによるECサイトのAPI基盤を設計・開発。"},
            {"project_name": "社内業務システム刷新", "period_start": "2022/01", "period_end": "2023/03",
             "team_size": 4, "role_title": "バックエンドエンジニア",
             "tech_stack": ["Python", "Django", "MySQL", "Docker"],
             "description": "レガシーシステムをDjangoベースにリプレイス。"},
        ],
        "skills": {"tools": ["VS Code", "Git", "Docker", "Postman"], "certifications": ["AWS Solutions Architect Associate"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "英語", "level": "ビジネスレベル"}]},
    },
    {
        "user_id": "eng_suzuki", "password": "pass123", "name": "鈴木 次郎", "specialty": "バックエンド開発",
        "work_location": "大阪府", "nearest_station": "梅田駅", "relocation_ok": 0,
        "school": "大阪大学 基礎工学部 情報科学科", "skill_level": "中級",
        "self_pr": "Javaを中心としたエンタープライズシステム開発に5年間従事。Spring Bootでの開発が得意です。",
        "hobbies": "将棋、カメラ",
        "career": [
            {"project_name": "金融機関向け口座管理システム", "period_start": "2022/04", "period_end": "2024/06",
             "team_size": 10, "role_title": "サブリーダー",
             "tech_stack": ["Java", "Spring Boot", "Oracle", "AWS"],
             "description": "口座管理の基幹システムを設計・開発。API連携基盤を担当。"},
        ],
        "skills": {"tools": ["IntelliJ IDEA", "Git", "Jenkins"], "certifications": ["Oracle Certified Java Programmer Gold"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },
    {
        "user_id": "eng_ito", "password": "pass123", "name": "伊藤 三郎", "specialty": "バックエンド開発",
        "work_location": "福岡県", "nearest_station": "博多駅", "relocation_ok": 1,
        "school": "九州大学 工学部 電気情報工学科", "skill_level": "上級",
        "self_pr": "Go言語でのマイクロサービス開発を3年以上経験。高パフォーマンスなシステム構築が強みです。",
        "hobbies": "サーフィン、料理",
        "career": [
            {"project_name": "決済プラットフォーム開発", "period_start": "2023/01", "period_end": "現在",
             "team_size": 8, "role_title": "バックエンドエンジニア",
             "tech_stack": ["Go", "gRPC", "Kubernetes", "GCP", "PostgreSQL"],
             "description": "決済APIのマイクロサービスをGo言語で開発。毎秒1万リクエスト規模の処理を実現。"},
        ],
        "skills": {"tools": ["GoLand", "Git", "Docker", "Terraform"], "certifications": ["Google Cloud Professional Cloud Architect"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "英語", "level": "日常会話"}]},
    },
    {
        "user_id": "eng_watanabe", "password": "pass123", "name": "渡辺 四郎", "specialty": "バックエンド開発",
        "work_location": "東京都", "nearest_station": "新宿駅", "relocation_ok": 0,
        "school": "早稲田大学 理工学部 情報通信学科", "skill_level": "中級",
        "self_pr": "Ruby on Railsでのアジャイル開発を得意とし、スタートアップでのプロダクト立ち上げ経験が豊富です。",
        "hobbies": "ギター、映画鑑賞",
        "career": [
            {"project_name": "SaaS型勤怠管理サービス開発", "period_start": "2022/06", "period_end": "2024/02",
             "team_size": 5, "role_title": "フルスタックエンジニア",
             "tech_stack": ["Ruby", "Rails", "PostgreSQL", "Redis", "AWS"],
             "description": "勤怠管理SaaSの新規開発。フロント〜バックエンドまで一貫して担当。"},
        ],
        "skills": {"tools": ["VS Code", "Git", "Docker", "Slack"], "certifications": [], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },
    {
        "user_id": "eng_yamamoto", "password": "pass123", "name": "山本 五郎", "specialty": "バックエンド開発",
        "work_location": "名古屋市", "nearest_station": "名古屋駅", "relocation_ok": 1,
        "school": "名古屋大学 情報学部", "skill_level": "上級",
        "self_pr": "C#/.NETでの業務システム開発を8年間経験。Azureクラウドへの移行プロジェクトも複数リード。",
        "hobbies": "テニス、旅行",
        "career": [
            {"project_name": "製造業向けERPシステム", "period_start": "2021/04", "period_end": "2024/03",
             "team_size": 12, "role_title": "プロジェクトリーダー",
             "tech_stack": ["C#", ".NET", "Azure", "SQL Server", "Docker"],
             "description": "オンプレERPのAzureクラウド移行を主導。マイクロサービス化とCI/CD導入。"},
        ],
        "skills": {"tools": ["Visual Studio", "Git", "Azure DevOps"], "certifications": ["Azure Solutions Architect Expert", "PMP"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "英語", "level": "ビジネスレベル"}]},
    },

    # ---- フロントエンド系 ----
    {
        "user_id": "eng_nakamura", "password": "pass123", "name": "中村 美咲", "specialty": "フロントエンド開発",
        "work_location": "東京都", "nearest_station": "六本木駅", "relocation_ok": 0,
        "school": "慶應義塾大学 環境情報学部", "skill_level": "上級",
        "self_pr": "React/TypeScriptによるSPA開発を5年間経験。UIデザインからパフォーマンス最適化まで対応可能です。",
        "hobbies": "ヨガ、イラスト",
        "career": [
            {"project_name": "ヘルスケアアプリUI刷新", "period_start": "2023/07", "period_end": "現在",
             "team_size": 4, "role_title": "フロントエンドリード",
             "tech_stack": ["React", "TypeScript", "Next.js", "Tailwind CSS", "Storybook"],
             "description": "ヘルスケアアプリのフロントエンドをNext.jsで全面リニューアル。"},
        ],
        "skills": {"tools": ["VS Code", "Figma", "Git", "Chrome DevTools"], "certifications": [], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "英語", "level": "日常会話"}]},
    },
    {
        "user_id": "eng_kobayashi", "password": "pass123", "name": "小林 大輔", "specialty": "フロントエンド開発",
        "work_location": "東京都", "nearest_station": "品川駅", "relocation_ok": 1,
        "school": "東京工業大学 情報理工学院", "skill_level": "中級",
        "self_pr": "Vue.js/Nuxt.jsでのフロントエンド開発を3年間経験。コンポーネント設計とテスト自動化に注力しています。",
        "hobbies": "ボルダリング、ゲーム",
        "career": [
            {"project_name": "不動産ポータルサイトリニューアル", "period_start": "2023/01", "period_end": "2024/06",
             "team_size": 6, "role_title": "フロントエンドエンジニア",
             "tech_stack": ["Vue.js", "Nuxt.js", "TypeScript", "Vuetify", "Jest"],
             "description": "不動産ポータルサイトのフロントエンドをVue 3で再構築。"},
        ],
        "skills": {"tools": ["VS Code", "Git", "Figma", "Cypress"], "certifications": [], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },
    {
        "user_id": "eng_kato", "password": "pass123", "name": "加藤 さくら", "specialty": "フロントエンド開発",
        "work_location": "横浜市", "nearest_station": "横浜駅", "relocation_ok": 0,
        "school": "横浜国立大学 理工学部", "skill_level": "中級",
        "self_pr": "Angular/RxJSを用いたエンタープライズ向けフロントエンド開発を3年間経験しています。",
        "hobbies": "ピアノ、カフェ巡り",
        "career": [
            {"project_name": "保険会社向け契約管理画面", "period_start": "2022/10", "period_end": "2024/09",
             "team_size": 8, "role_title": "フロントエンドエンジニア",
             "tech_stack": ["Angular", "TypeScript", "RxJS", "Angular Material"],
             "description": "保険契約管理システムのフロントエンドをAngularで開発。複雑なフォームバリデーション実装。"},
        ],
        "skills": {"tools": ["WebStorm", "Git", "Jira"], "certifications": [], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "韓国語", "level": "日常会話"}]},
    },

    # ---- フルスタック系 ----
    {
        "user_id": "eng_yoshida", "password": "pass123", "name": "吉田 健太", "specialty": "フルスタック開発",
        "work_location": "東京都", "nearest_station": "秋葉原駅", "relocation_ok": 1,
        "school": "筑波大学 情報学群", "skill_level": "上級",
        "self_pr": "React+Node.jsのフルスタック開発を6年間経験。AWS上でのインフラ構築からフロントまで一貫して対応。",
        "hobbies": "自作PC、アニメ",
        "career": [
            {"project_name": "オンライン教育プラットフォーム", "period_start": "2022/04", "period_end": "現在",
             "team_size": 7, "role_title": "フルスタックエンジニア",
             "tech_stack": ["React", "Node.js", "TypeScript", "MongoDB", "AWS", "Docker"],
             "description": "リアルタイム動画配信を含むオンライン教育プラットフォームの全機能を開発。"},
        ],
        "skills": {"tools": ["VS Code", "Git", "Docker", "AWS CLI"], "certifications": ["AWS Developer Associate"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "英語", "level": "ビジネスレベル"}]},
    },
    {
        "user_id": "eng_sasaki", "password": "pass123", "name": "佐々木 遥", "specialty": "フルスタック開発",
        "work_location": "札幌市", "nearest_station": "札幌駅", "relocation_ok": 0,
        "school": "北海道大学 工学部", "skill_level": "中級",
        "self_pr": "PHP/Laravelでのバックエンドと、Vue.jsでのフロントエンド開発を両立できるフルスタックエンジニアです。",
        "hobbies": "スキー、写真撮影",
        "career": [
            {"project_name": "飲食店予約管理システム", "period_start": "2023/04", "period_end": "2024/08",
             "team_size": 4, "role_title": "リードエンジニア",
             "tech_stack": ["PHP", "Laravel", "Vue.js", "MySQL", "Docker"],
             "description": "飲食店向け予約管理システムをLaravel+Vue.jsで新規開発。"},
        ],
        "skills": {"tools": ["PhpStorm", "Git", "Docker", "TablePlus"], "certifications": ["PHP技術者認定上級"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },

    # ---- インフラ / DevOps 系 ----
    {
        "user_id": "eng_maeda", "password": "pass123", "name": "前田 翔太", "specialty": "インフラ / DevOps",
        "work_location": "東京都", "nearest_station": "東京駅", "relocation_ok": 1,
        "school": "東京理科大学 理工学部", "skill_level": "上級",
        "self_pr": "AWS/Terraformを中心としたクラウドインフラの設計・構築・運用を7年間経験。大規模環境のIaC化が得意です。",
        "hobbies": "登山、コーヒー",
        "career": [
            {"project_name": "マルチアカウントAWS環境構築", "period_start": "2023/01", "period_end": "現在",
             "team_size": 5, "role_title": "インフラアーキテクト",
             "tech_stack": ["AWS", "Terraform", "Docker", "Kubernetes", "GitHub Actions"],
             "description": "AWS Organizations / Control Towerを用いたマルチアカウント環境の設計と構築。"},
        ],
        "skills": {"tools": ["VS Code", "Git", "Terraform Cloud", "Datadog"], "certifications": ["AWS Solutions Architect Professional", "CKA"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "英語", "level": "ビジネスレベル"}]},
    },
    {
        "user_id": "eng_ogawa", "password": "pass123", "name": "小川 真由", "specialty": "インフラ / DevOps",
        "work_location": "東京都", "nearest_station": "目黒駅", "relocation_ok": 0,
        "school": "お茶の水女子大学 理学部", "skill_level": "中級",
        "self_pr": "GCP環境でのKubernetesクラスタ運用とCI/CDパイプライン構築を3年間担当。SREの知見もあります。",
        "hobbies": "園芸、ボードゲーム",
        "career": [
            {"project_name": "動画配信サービスインフラ最適化", "period_start": "2022/07", "period_end": "2024/06",
             "team_size": 6, "role_title": "SREエンジニア",
             "tech_stack": ["GCP", "Kubernetes", "Docker", "Prometheus", "Grafana"],
             "description": "動画配信サービスのGKE基盤運用とオートスケーリング最適化を担当。"},
        ],
        "skills": {"tools": ["VS Code", "Git", "Helm", "ArgoCD"], "certifications": ["Google Cloud Professional Cloud DevOps Engineer"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },
    {
        "user_id": "eng_murakami", "password": "pass123", "name": "村上 拓海", "specialty": "インフラ / DevOps",
        "work_location": "大阪府", "nearest_station": "なんば駅", "relocation_ok": 1,
        "school": "関西大学 システム理工学部", "skill_level": "中級",
        "self_pr": "Azure環境でのインフラ構築とCI/CD導入を4年間経験。オンプレからクラウドへの移行案件を得意とします。",
        "hobbies": "フットサル、釣り",
        "career": [
            {"project_name": "製薬会社Azure移行プロジェクト", "period_start": "2022/10", "period_end": "2024/09",
             "team_size": 8, "role_title": "インフラエンジニア",
             "tech_stack": ["Azure", "Terraform", "Docker", "Azure DevOps", "Linux"],
             "description": "オンプレミスの研究データ管理基盤をAzureへ移行。セキュリティ要件に準拠した設計を実施。"},
        ],
        "skills": {"tools": ["VS Code", "Git", "Azure CLI", "Ansible"], "certifications": ["Azure Administrator Associate"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },

    # ---- モバイル系 ----
    {
        "user_id": "eng_fujita", "password": "pass123", "name": "藤田 あかり", "specialty": "モバイル開発",
        "work_location": "東京都", "nearest_station": "恵比寿駅", "relocation_ok": 0,
        "school": "上智大学 理工学部", "skill_level": "上級",
        "self_pr": "Swift/SwiftUIでのiOSアプリ開発を5年間経験。App Storeランキング上位アプリの開発実績あり。",
        "hobbies": "ダンス、映画鑑賞",
        "career": [
            {"project_name": "フィットネスアプリ開発", "period_start": "2023/01", "period_end": "現在",
             "team_size": 5, "role_title": "iOSリードエンジニア",
             "tech_stack": ["Swift", "SwiftUI", "Firebase", "Core Data"],
             "description": "ヘルスケア連携機能を持つフィットネスアプリのiOS版を開発・運用。"},
        ],
        "skills": {"tools": ["Xcode", "Git", "Instruments", "Figma"], "certifications": [], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "英語", "level": "日常会話"}]},
    },
    {
        "user_id": "eng_hasegawa", "password": "pass123", "name": "長谷川 翼", "specialty": "モバイル開発",
        "work_location": "東京都", "nearest_station": "池袋駅", "relocation_ok": 1,
        "school": "東京電機大学 工学部", "skill_level": "中級",
        "self_pr": "Kotlin/Jetpack ComposeでのAndroidアプリ開発を3年間経験。クリーンアーキテクチャを重視した設計が得意です。",
        "hobbies": "サッカー観戦、DIY",
        "career": [
            {"project_name": "配送管理モバイルアプリ", "period_start": "2023/04", "period_end": "2024/10",
             "team_size": 4, "role_title": "Androidエンジニア",
             "tech_stack": ["Kotlin", "Jetpack Compose", "Firebase", "Google Maps API"],
             "description": "配送ドライバー向けルート最適化・管理アプリをKotlinで開発。"},
        ],
        "skills": {"tools": ["Android Studio", "Git", "Firebase Console"], "certifications": ["Associate Android Developer"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },
    {
        "user_id": "eng_morita", "password": "pass123", "name": "森田 陽菜", "specialty": "モバイル開発",
        "work_location": "横浜市", "nearest_station": "みなとみらい駅", "relocation_ok": 0,
        "school": "横浜市立大学 データサイエンス学部", "skill_level": "中級",
        "self_pr": "Flutter/Dartでのクロスプラットフォーム開発を2年半経験。1つのコードベースでiOS/Androidの両方に対応。",
        "hobbies": "水彩画、ヨガ",
        "career": [
            {"project_name": "美容院予約アプリ開発", "period_start": "2023/06", "period_end": "現在",
             "team_size": 3, "role_title": "モバイルエンジニア",
             "tech_stack": ["Flutter", "Dart", "Firebase", "Stripe API"],
             "description": "美容院の予約・決済アプリをFlutterで開発。プッシュ通知やカレンダー連携を実装。"},
        ],
        "skills": {"tools": ["VS Code", "Git", "Firebase", "Figma"], "certifications": [], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "中国語", "level": "日常会話"}]},
    },

    # ---- データ / AI / ML 系 ----
    {
        "user_id": "eng_kimura", "password": "pass123", "name": "木村 隆", "specialty": "データエンジニアリング",
        "work_location": "東京都", "nearest_station": "大手町駅", "relocation_ok": 1,
        "school": "東京大学大学院 情報理工学系研究科", "skill_level": "上級",
        "self_pr": "Python/Sparkを用いたデータパイプライン構築と大規模データ分析基盤の設計・運用を6年間経験。",
        "hobbies": "数学、チェス",
        "career": [
            {"project_name": "広告配信データ基盤構築", "period_start": "2022/04", "period_end": "現在",
             "team_size": 6, "role_title": "データエンジニア",
             "tech_stack": ["Python", "Apache Spark", "Airflow", "BigQuery", "GCP"],
             "description": "日次数十億レコードの広告配信ログを処理するETLパイプラインを設計・構築。"},
        ],
        "skills": {"tools": ["Jupyter", "Git", "dbt", "Looker"], "certifications": ["Google Cloud Professional Data Engineer"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "英語", "level": "ビジネスレベル"}]},
    },
    {
        "user_id": "eng_hayashi", "password": "pass123", "name": "林 彩花", "specialty": "機械学習エンジニア",
        "work_location": "東京都", "nearest_station": "本郷三丁目駅", "relocation_ok": 0,
        "school": "東京大学大学院 工学系研究科", "skill_level": "上級",
        "self_pr": "自然言語処理と画像認識のモデル開発・運用を4年間経験。MLOps基盤の構築にも精通しています。",
        "hobbies": "論文読み、猫カフェ",
        "career": [
            {"project_name": "チャットボットAIエンジン開発", "period_start": "2023/01", "period_end": "現在",
             "team_size": 5, "role_title": "MLエンジニア",
             "tech_stack": ["Python", "PyTorch", "FastAPI", "Docker", "AWS SageMaker"],
             "description": "大規模言語モデルのファインチューニングとAPI化。レスポンス最適化を担当。"},
        ],
        "skills": {"tools": ["Jupyter", "Git", "MLflow", "Weights & Biases"], "certifications": ["AWS Machine Learning Specialty"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "英語", "level": "ビジネスレベル"}]},
    },
    {
        "user_id": "eng_shimizu", "password": "pass123", "name": "清水 大地", "specialty": "データサイエンス",
        "work_location": "東京都", "nearest_station": "五反田駅", "relocation_ok": 1,
        "school": "統計数理研究所（修了）", "skill_level": "上級",
        "self_pr": "統計モデリングとA/Bテスト設計を専門に5年間活動。ビジネスKPI改善に直結する分析を行います。",
        "hobbies": "麻雀、ワイン",
        "career": [
            {"project_name": "ECサイトレコメンドエンジン改善", "period_start": "2022/10", "period_end": "2024/09",
             "team_size": 4, "role_title": "データサイエンティスト",
             "tech_stack": ["Python", "scikit-learn", "Pandas", "BigQuery", "Looker"],
             "description": "レコメンドアルゴリズムの精度改善とA/Bテスト設計。CVR15%改善を達成。"},
        ],
        "skills": {"tools": ["Jupyter", "Git", "Tableau", "BigQuery"], "certifications": ["統計検定1級"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },

    # ---- セキュリティ系 ----
    {
        "user_id": "eng_takahashi", "password": "pass123", "name": "高橋 優", "specialty": "セキュリティエンジニア",
        "work_location": "東京都", "nearest_station": "神田駅", "relocation_ok": 0,
        "school": "千葉大学 工学部", "skill_level": "上級",
        "self_pr": "Webアプリケーションの脆弱性診断とペネトレーションテストを5年間実施。セキュアコーディングの研修講師も務めています。",
        "hobbies": "CTF、読書",
        "career": [
            {"project_name": "金融機関向けセキュリティ診断", "period_start": "2022/04", "period_end": "現在",
             "team_size": 4, "role_title": "セキュリティコンサルタント",
             "tech_stack": ["Python", "Burp Suite", "OWASP ZAP", "Docker", "Linux"],
             "description": "金融機関のWebアプリに対する定期的な脆弱性診断・ペネトレーションテストを実施。"},
        ],
        "skills": {"tools": ["Burp Suite", "Kali Linux", "Wireshark", "Git"], "certifications": ["情報処理安全確保支援士", "OSCP"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "英語", "level": "ビジネスレベル"}]},
    },

    # ---- 組み込み / IoT 系 ----
    {
        "user_id": "eng_inoue", "password": "pass123", "name": "井上 聡", "specialty": "組み込み / IoT",
        "work_location": "愛知県", "nearest_station": "豊田市駅", "relocation_ok": 0,
        "school": "名古屋工業大学 工学部", "skill_level": "上級",
        "self_pr": "C/C++による組み込みファームウェア開発を10年間経験。自動車ECU開発からIoTゲートウェイまで幅広く対応。",
        "hobbies": "電子工作、キャンプ",
        "career": [
            {"project_name": "車載ECUファームウェア開発", "period_start": "2021/04", "period_end": "現在",
             "team_size": 15, "role_title": "組み込みリードエンジニア",
             "tech_stack": ["C", "C++", "RTOS", "CAN", "AUTOSAR"],
             "description": "車載通信ECUのファームウェアを開発。AUTOSAR準拠のソフトウェアアーキテクチャを設計。"},
        ],
        "skills": {"tools": ["Eclipse", "Git", "JIRA", "Oscilloscope"], "certifications": ["エンベデッドシステムスペシャリスト"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },

    # ---- ゲーム系 ----
    {
        "user_id": "eng_nishida", "password": "pass123", "name": "西田 遼", "specialty": "ゲーム開発",
        "work_location": "東京都", "nearest_station": "中野駅", "relocation_ok": 1,
        "school": "デジタルハリウッド大学", "skill_level": "中級",
        "self_pr": "Unity/C#でのモバイルゲーム開発を4年間経験。3Dグラフィックスとパフォーマンス最適化が得意です。",
        "hobbies": "ゲーム、3Dモデリング",
        "career": [
            {"project_name": "モバイルRPG開発", "period_start": "2022/04", "period_end": "2024/06",
             "team_size": 12, "role_title": "クライアントエンジニア",
             "tech_stack": ["Unity", "C#", "Firebase", "Jenkins"],
             "description": "モバイル向けRPGのクライアント側開発。シェーダープログラミングとUI実装を担当。"},
        ],
        "skills": {"tools": ["Unity", "Git", "Blender", "Photoshop"], "certifications": ["Unity Certified Developer"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },

    # ---- QA / テスト 系 ----
    {
        "user_id": "eng_okada", "password": "pass123", "name": "岡田 麻衣", "specialty": "QA / テストエンジニア",
        "work_location": "東京都", "nearest_station": "浜松町駅", "relocation_ok": 0,
        "school": "法政大学 情報科学部", "skill_level": "中級",
        "self_pr": "Seleniumを用いたE2Eテスト自動化とCI/CDパイプラインへの組み込みを3年間経験。テスト戦略の策定も可能です。",
        "hobbies": "読書、ハンドメイド",
        "career": [
            {"project_name": "ECサイトテスト自動化プロジェクト", "period_start": "2023/01", "period_end": "現在",
             "team_size": 4, "role_title": "QAリード",
             "tech_stack": ["Python", "Selenium", "Pytest", "GitHub Actions", "Docker"],
             "description": "ECサイトのリグレッションテスト自動化基盤を構築。テスト実行時間を70%短縮。"},
        ],
        "skills": {"tools": ["VS Code", "Git", "Jira", "TestRail"], "certifications": ["JSTQB Foundation"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },

    # ---- PM / スクラムマスター系 ----
    {
        "user_id": "eng_ueda", "password": "pass123", "name": "上田 浩二", "specialty": "プロジェクトマネジメント",
        "work_location": "東京都", "nearest_station": "虎ノ門駅", "relocation_ok": 1,
        "school": "一橋大学 商学部", "skill_level": "上級",
        "self_pr": "アジャイル/スクラム開発のPMを7年間経験。30名規模のチームを率いた実績があります。技術バックグラウンドはJava。",
        "hobbies": "ゴルフ、ワイン",
        "career": [
            {"project_name": "大手小売DXプロジェクト", "period_start": "2022/04", "period_end": "現在",
             "team_size": 25, "role_title": "プロジェクトマネージャー",
             "tech_stack": ["Java", "Spring Boot", "React", "AWS", "Docker"],
             "description": "小売業のDX推進プロジェクト全体を統括。複数チームの調整とステークホルダー管理を担当。"},
        ],
        "skills": {"tools": ["Jira", "Confluence", "Miro", "Slack"], "certifications": ["PMP", "認定スクラムマスター (CSM)"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "英語", "level": "ビジネスレベル"}]},
    },

    # ---- 追加バックエンド (Rust, PHP) ----
    {
        "user_id": "eng_endo", "password": "pass123", "name": "遠藤 亮", "specialty": "バックエンド開発",
        "work_location": "東京都", "nearest_station": "御茶ノ水駅", "relocation_ok": 1,
        "school": "電気通信大学 情報理工学域", "skill_level": "中級",
        "self_pr": "Rustによる高性能バックエンド開発を2年間経験。メモリ安全性と処理速度を両立した実装が得意です。",
        "hobbies": "ロードバイク、コーヒー焙煎",
        "career": [
            {"project_name": "リアルタイム株価配信システム", "period_start": "2023/06", "period_end": "現在",
             "team_size": 4, "role_title": "バックエンドエンジニア",
             "tech_stack": ["Rust", "Tokio", "Redis", "PostgreSQL", "Docker"],
             "description": "WebSocketベースのリアルタイム株価配信サーバーをRustで実装。低レイテンシを実現。"},
        ],
        "skills": {"tools": ["VS Code", "Git", "Docker", "Grafana"], "certifications": [], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },
    {
        "user_id": "eng_aoki", "password": "pass123", "name": "青木 彩", "specialty": "バックエンド開発",
        "work_location": "仙台市", "nearest_station": "仙台駅", "relocation_ok": 0,
        "school": "東北大学 工学部", "skill_level": "中級",
        "self_pr": "PHP/Laravelを中心としたWebアプリケーション開発を4年間経験。ECサイトやCMS構築の実績が豊富です。",
        "hobbies": "温泉巡り、牛タン食べ歩き",
        "career": [
            {"project_name": "ECモール出店管理システム", "period_start": "2022/07", "period_end": "2024/06",
             "team_size": 5, "role_title": "バックエンドエンジニア",
             "tech_stack": ["PHP", "Laravel", "MySQL", "Redis", "AWS"],
             "description": "複数ECモールの在庫・受注を一元管理するシステムをLaravelで開発。"},
        ],
        "skills": {"tools": ["PhpStorm", "Git", "Docker", "Redis Insight"], "certifications": ["PHP技術者認定初級"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },

    # ---- 追加フロントエンド (Svelte) ----
    {
        "user_id": "eng_matsumoto", "password": "pass123", "name": "松本 凛", "specialty": "フロントエンド開発",
        "work_location": "京都市", "nearest_station": "京都駅", "relocation_ok": 1,
        "school": "京都大学 工学部 情報学科", "skill_level": "中級",
        "self_pr": "Svelte/SvelteKitを用いた軽量フロントエンド開発を2年間経験。パフォーマンスファーストの開発思想で取り組んでいます。",
        "hobbies": "茶道、散歩",
        "career": [
            {"project_name": "旅行プランニングWebアプリ", "period_start": "2023/04", "period_end": "現在",
             "team_size": 3, "role_title": "フロントエンドエンジニア",
             "tech_stack": ["Svelte", "SvelteKit", "TypeScript", "Tailwind CSS", "Supabase"],
             "description": "旅行プランの作成・共有Webアプリのフロントエンドを開発。SSR対応。"},
        ],
        "skills": {"tools": ["VS Code", "Git", "Figma", "Vercel"], "certifications": [], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "フランス語", "level": "日常会話"}]},
    },

    # ---- 追加インフラ (オンプレ + Linux) ----
    {
        "user_id": "eng_saito", "password": "pass123", "name": "斎藤 誠", "specialty": "インフラエンジニア",
        "work_location": "東京都", "nearest_station": "田町駅", "relocation_ok": 0,
        "school": "芝浦工業大学 工学部", "skill_level": "上級",
        "self_pr": "Linux/オンプレミス環境の設計・構築を10年以上経験。ネットワーク設計からミドルウェアチューニングまで対応可能。",
        "hobbies": "自作サーバー、家庭菜園",
        "career": [
            {"project_name": "大手通信キャリアNW基盤構築", "period_start": "2020/04", "period_end": "2024/03",
             "team_size": 20, "role_title": "シニアインフラエンジニア",
             "tech_stack": ["Linux", "Ansible", "Nginx", "PostgreSQL", "Zabbix"],
             "description": "通信キャリアの大規模Linux基盤の設計・構築・運用。約500台のサーバー管理。"},
        ],
        "skills": {"tools": ["Vim", "Git", "Ansible", "Zabbix"], "certifications": ["LPIC Level 3", "CCNP"], "language_skills": [{"language": "日本語", "level": "ネイティブ"}]},
    },

    # ---- 追加フルスタック (Next.js + Python) ----
    {
        "user_id": "eng_fukuda", "password": "pass123", "name": "福田 真希", "specialty": "フルスタック開発",
        "work_location": "東京都", "nearest_station": "表参道駅", "relocation_ok": 1,
        "school": "津田塾大学 学芸学部 情報科学科", "skill_level": "中級",
        "self_pr": "Next.js+Python(FastAPI)でのフルスタック開発を3年間経験。デザインシステム構築にも携わっています。",
        "hobbies": "美術館巡り、ヨガ",
        "career": [
            {"project_name": "HR SaaSプロダクト開発", "period_start": "2023/01", "period_end": "現在",
             "team_size": 6, "role_title": "フルスタックエンジニア",
             "tech_stack": ["Next.js", "TypeScript", "Python", "FastAPI", "PostgreSQL", "AWS"],
             "description": "人事管理SaaSのフルスタック開発。フロントはNext.js、バックエンドはFastAPIで構築。"},
        ],
        "skills": {"tools": ["VS Code", "Git", "Figma", "Storybook"], "certifications": [], "language_skills": [{"language": "日本語", "level": "ネイティブ"}, {"language": "英語", "level": "日常会話"}]},
    },
]
# fmt: on


def insert_seed_engineers() -> None:
    """シードデータを DB に投入する（users / engineers / skill_sheets / hearing_logs）"""
    from passlib.hash import bcrypt

    conn_mod = __import__("db.database", fromlist=["get_connection"])
    conn = conn_mod.get_connection()
    now = "2025-01-01T00:00:00"

    for eng in SEED_ENGINEERS:
        uid = eng["user_id"]

        # --- users ---
        existing = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (uid,)).fetchone()
        if existing:
            continue

        conn.execute(
            "INSERT INTO users (user_id, password_hash, name, role) VALUES (?, ?, ?, ?)",
            (uid, bcrypt.hash(eng["password"]), eng["name"], "engineer"),
        )

        # --- engineers ---
        school_parts = eng.get("school", "").split(" ", 2)
        school_name = school_parts[0] if len(school_parts) > 0 else ""
        faculty_name = school_parts[1] if len(school_parts) > 1 else ""
        department_name = school_parts[2] if len(school_parts) > 2 else ""

        conn.execute(
            "INSERT INTO engineers (engineer_id, specialty, relocation_ok, work_location, "
            "nearest_station, school_name, faculty_name, department_name, "
            "self_pr, hobbies, skill_level) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (uid, eng["specialty"], eng.get("relocation_ok", 0), eng.get("work_location", ""),
             eng.get("nearest_station", ""), school_name, faculty_name, department_name,
             eng.get("self_pr", ""), eng.get("hobbies", ""), eng.get("skill_level", "")),
        )

        # --- skill_sheets (basic) ---
        basic_data = {
            "specialty": eng["specialty"],
            "relocation_ok": eng.get("relocation_ok", 0),
            "work_location": eng.get("work_location", ""),
            "nearest_station": eng.get("nearest_station", ""),
            "school_name": school_name,
            "faculty_name": faculty_name,
            "department_name": department_name,
            "self_pr": eng.get("self_pr", ""),
            "hobbies": eng.get("hobbies", ""),
            "skill_level": eng.get("skill_level", ""),
        }
        conn.execute(
            "INSERT INTO skill_sheets (engineer_id, theme, raw_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (uid, "basic", json.dumps(basic_data, ensure_ascii=False), now, now),
        )

        # --- skill_sheets (career) ---
        career_data = {"experiences": eng.get("career", [])}
        conn.execute(
            "INSERT INTO skill_sheets (engineer_id, theme, raw_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (uid, "career", json.dumps(career_data, ensure_ascii=False), now, now),
        )

        # --- skill_sheets (skills) ---
        skills_data = eng.get("skills", {})
        conn.execute(
            "INSERT INTO skill_sheets (engineer_id, theme, raw_data, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (uid, "skills", json.dumps(skills_data, ensure_ascii=False), now, now),
        )

        # --- hearing_logs (全テーマ完了済み) ---
        for theme in ["basic", "career", "skills"]:
            conn.execute(
                "INSERT INTO hearing_logs (engineer_id, theme, messages, completed, completed_at) VALUES (?, ?, ?, ?, ?)",
                (uid, theme, "[]", 1, now),
            )

    conn.commit()
    conn.close()
