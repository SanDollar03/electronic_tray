# app.py  ― 電子トレー（文書回覧）アプリ 2025-06-01 版
# -------------------------------------------------------

import os
import csv
import uuid
import hashlib
import datetime as dt
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, abort, flash, send_from_directory
)
from werkzeug.utils import secure_filename

# ───────── 設定 ────────────────────────────────
APP_DIR    = os.path.abspath(os.path.dirname(__file__))
DATA_DIR   = os.path.join(APP_DIR, "data")
ATTACH_DIR = os.path.join(DATA_DIR, "attachments")

os.makedirs(ATTACH_DIR, exist_ok=True)

USERS_CSV   = os.path.join(DATA_DIR, "users.csv")
LETTERS_CSV = os.path.join(DATA_DIR, "letters.csv")
FILES_CSV   = os.path.join(DATA_DIR, "files.csv")

PORT        = 5100
SECRET_KEY  = "change-this-key"          # 運用時はランダム文字列に変更
ALLOWED_EXT = {"pdf", "docx", "xlsx", "png", "jpg", "zip"}

# ───────── ユーティリティ ─────────────────────
def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def read_csv(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))

def append_csv(path: str, row: dict) -> None:
    is_new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if is_new:
            w.writeheader()
        w.writerow(row)

def write_csv(path: str, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

def login_required(fn):
    @wraps(fn)
    def _wrap(*a, **kw):
        if not session.get("uid"):
            return redirect(url_for("login"))
        return fn(*a, **kw)
    return _wrap

# ───────── Flask アプリ ───────────────────────
app = Flask(__name__, static_folder="static")
app.secret_key = SECRET_KEY

# ── トップ ────────────────────────────────────
@app.route("/")
def index():
    return redirect(url_for("letters") if session.get("uid") else url_for("login"))

# ── 認証関連 ─────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    email = request.form["email"].strip().lower()
    name  = request.form["name"].strip()
    pw1, pw2 = request.form["pw1"], request.form["pw2"]

    if pw1 != pw2:
        flash("パスワードが一致しません")
        return redirect(url_for("register"))

    if any(u["email"] == email for u in read_csv(USERS_CSV)):
        flash("既に登録済みのメールアドレスです")
        return redirect(url_for("register"))

    uid = str(uuid.uuid4())
    append_csv(USERS_CSV, {
        "id": uid,
        "email": email,
        "display_name": name,
        "pw_hash": sha256(pw1)
    })
    flash("登録完了。ログインしてください。")
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form["email"].strip().lower()
    pw    = sha256(request.form["pw"])

    user = next(
        (u for u in read_csv(USERS_CSV)
         if u["email"] == email and u["pw_hash"] == pw),
        None
    )
    if not user:
        flash("メールアドレスまたはパスワードが違います")
        return redirect(url_for("login"))

    session["uid"] = user["id"]
    return redirect(url_for("letters"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── 文書一覧 ─────────────────────────────────
@app.route("/letters")
@login_required
def letters():
    uid      = session["uid"]
    letters  = read_csv(LETTERS_CSV)
    users    = {u["id"]: u for u in read_csv(USERS_CSV)}

    sent, inbox = [], []

    for l in letters:
        assignees = l["assignee_ids"].split(",")
        cur_idx   = int(l["current_index"])
        cur_uid   = assignees[cur_idx] if cur_idx < len(assignees) else ""
        u         = users.get(cur_uid)
        cur_disp  = f"{u['display_name']} ({u['email']})" if u else "—"

        row = l.copy()
        row["current_uid"]     = cur_uid
        row["current_display"] = cur_disp

        if l["sender_id"] == uid:
            sent.append(row)
        if uid in assignees:
            inbox.append(row)

    return render_template(
        "letters.html",
        sent=sent,
        inbox=inbox,
        uid=uid
    )

# ── 文書新規作成 ───────────────────────────────
@app.route("/letters/new", methods=["GET", "POST"])
@login_required
def letter_new():
    if request.method == "GET":
        return render_template("letter_new.html", users=read_csv(USERS_CSV))

    uid        = session["uid"]         # ← ここで uid を取得
    title      = request.form["title"][:20]
    assignees  = request.form.getlist("assignees")[:10]

    if not assignees:
        flash("担当者を最低 1 名選択してください")
        return redirect(url_for("letter_new"))

    lid = str(uuid.uuid4())
    os.makedirs(os.path.join(ATTACH_DIR, lid), exist_ok=True)

    # 添付ファイル保存
    for f in request.files.getlist("files"):
        if not f or f.filename == "":
            continue
        ext = f.filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXT:
            flash(f"{f.filename} は許可されていない拡張子です")
            continue
        stored = f"{uuid.uuid4()}_{secure_filename(f.filename)}"
        f.save(os.path.join(ATTACH_DIR, lid, stored))
        append_csv(FILES_CSV, {
            "id": str(uuid.uuid4()),
            "letter_id": lid,
            "orig_name": f.filename,
            "stored_name": stored
        })

    # 文書メタ保存
    append_csv(LETTERS_CSV, {
        "id": lid,
        "title": title,
        "sender_id": uid,
        "assignee_ids": ",".join(assignees),
        "current_index": "0",
        "status": "in_progress",
        "created_at": dt.datetime.now().isoformat()
    })

    flash("文書を発行しました")
    return redirect(url_for("letters"))

# ── 文書詳細 ─────────────────────────────────
@app.route("/letters/<lid>")
@login_required
def letter_detail(lid):
    letter = next((l for l in read_csv(LETTERS_CSV) if l["id"] == lid), None)
    if not letter:
        abort(404)

    assignees = letter["assignee_ids"].split(",")
    cur_idx   = int(letter["current_index"])
    files     = [f for f in read_csv(FILES_CSV) if f["letter_id"] == lid]

    return render_template(
        "letter_detail.html",
        letter=letter,
        assignees=assignees,
        cur_idx=cur_idx,
        files=files,
        uid=session["uid"]
    )

# ── 次の担当者へ回す ──────────────────────────
@app.route("/letters/<lid>/advance", methods=["POST"])
@login_required
def letter_advance(lid):
    letters = read_csv(LETTERS_CSV)
    updated = False

    for l in letters:
        if l["id"] != lid:
            continue
        assignees = l["assignee_ids"].split(",")
        cur_idx   = int(l["current_index"])

        # 自分が現在の担当者でない場合は権限なし
        if assignees[cur_idx] != session["uid"]:
            abort(403)

        if cur_idx + 1 < len(assignees):
            l["current_index"] = str(cur_idx + 1)
        else:
            l["status"] = "finished"

        updated = True
        break

    if updated:
        write_csv(LETTERS_CSV, letters)
        flash("次の担当者へ回しました")

    return redirect(url_for("letter_detail", lid=lid))

# ── 添付ファイルダウンロード ─────────────────
@app.route("/files/<lid>/<stored_name>")
@login_required
def download_file(lid, stored_name):
    return send_from_directory(
        os.path.join(ATTACH_DIR, lid),
        stored_name,
        as_attachment=True
    )

# ───────── アプリ起動 ─────────────────────
if __name__ == "__main__":
    app.run(port=PORT, debug=True)
