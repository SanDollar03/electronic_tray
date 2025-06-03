electronic_tray/                     
├── app.py                           ← Flask
├── requirements.txt                 ← ライブラリ一
│
├── data/                            
│   ├── users.csv                    ← ユーザー情報
│   ├── letters.csv                  ← 文書メタ情報
│   └── attachments/                 ← ファイル保存用
│
├── templates/                       ← 
│   ├── base.html                    ← 共通
│   ├── login.html                   ← ログイン
│   ├── register.html                ← 新規登録
│   ├── letters.html                 ← 文書一覧
│   ├── letter_new.html              ← 文書新規作成
│   └── letter_detail.html           ← 文書詳細
│
└── static/
    ├── css/
    │   └── main.css                 
    └── js/
        └── main.js                  


python -m venv electronic_tray
cd electronic_tray
.\Scripts\activate       # mac/linux は source bin/activate

pip install flask==3.0.3 werkzeug email-validator
pip freeze > requirements.txt
