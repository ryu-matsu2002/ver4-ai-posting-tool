# 📁 ファイルパス: app/routes/site.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Site

# site_bp Blueprintの設定
site_bp = Blueprint("site", __name__)

@site_bp.route("/add", methods=["GET", "POST"])  # /site/add のパスを変更
@login_required
def add_site():
    if request.method == "POST":
        # フォームからの入力値を取得
        name = request.form.get("name")
        url = request.form.get("url", "").rstrip("/")  # 末尾のスラッシュを除去
        username = request.form.get("username")
        app_password = request.form.get("app_password")

        # 必要項目が全て入力されているかチェック
        if not name or not url or not username or not app_password:
            flash("すべての項目を入力してください。", "error")
            return redirect(url_for("site.add_site"))

        # サイトを新規登録
        new_site = Site(
            user_id=current_user.id,
            name=name,
            url=url,
            username=username,
            app_password=app_password
        )
        db.session.add(new_site)
        db.session.commit()

        flash("✅ サイトを登録しました！", "success")
        return redirect(url_for("dashboard.dashboard"))  # ダッシュボードにリダイレクト

    return render_template("add_site.html")  # サイト追加ページを表示
