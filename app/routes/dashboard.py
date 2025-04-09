# 📁 ファイルパス: app/routes/dashboard.py

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.models import ScheduledPost, Site

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    # 1. クエリパラメータから選択中のサイトIDを取得
    selected_site_id = request.args.get("site_id", type=int)

    # 2. 現在のユーザーが持つ全サイトを取得
    sites = Site.query.filter_by(user_id=current_user.id).all()

    # 3. サイトが1つもなければサイト設定ページに誘導
    if not sites:
        return redirect(url_for("site_settings"))

    # 4. site_idが未指定の場合は最初のサイトを選択状態に
    if not selected_site_id:
        selected_site_id = sites[0].id

    # 5. 投稿数（全体）を取得
    total_posts = ScheduledPost.query.filter_by(user_id=current_user.id).count()

    # 6. サイトごとの投稿数を集計
    post_counts = {
        site.id: ScheduledPost.query.filter_by(user_id=current_user.id, site_id=site.id).count()
        for site in sites
    }

    # 7. テンプレートへ値を渡す
    return render_template(
        "dashboard.html",
        sites=sites,
        selected_site_id=selected_site_id,
        total_posts=total_posts,
        post_counts=post_counts
    )
