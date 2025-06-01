electronic_tray/                     ← プロジェクトのルート
├── app.py                           ← Flask 本体（最新版）
├── requirements.txt                 ← ライブラリ一覧
│
├── data/                            ← すべて CSV & 添付を格納
│   ├── users.csv                    ← ユーザー情報（ヘッダーのみ可）
│   ├── letters.csv                  ← 文書メタ情報（ヘッダーのみ可）
│   └── attachments/                 ← 実ファイル保存用（文書ごとにサブフォルダ）
│
├── templates/                       ← 画面テンプレート
│   ├── base.html                    ← 共通レイアウト
│   ├── login.html                   ← ログイン画面
│   ├── register.html                ← 新規登録画面
│   ├── letters.html                 ← 文書一覧
│   ├── letter_new.html              ← 文書新規作成（検索＋添付 UI 付き）
│   └── letter_detail.html           ← 文書詳細
│
└── static/
    ├── css/
    │   └── main.css                 ← 共通スタイル
    └── js/
        └── main.js                  ← 担当者 & 添付ファイル操作用 JS


python -m venv electronic_tray
cd electronic_tray
. Scripts/activate       # mac/linux は source bin/activate

pip install flask==3.0.3 werkzeug email-validator
pip freeze > requirements.txt

python app.py
# ブラウザで http://localhost:5100
