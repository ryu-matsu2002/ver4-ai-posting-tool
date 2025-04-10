from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.models import ScheduledPost, Site

# dashboard_bpを適切に設定
dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard", methods=["GET", "POST"])  # ✅ POST対応を追加
@login_required
def dashboard():
    # 選択されたサイトIDを取得（GETパラメータ or POSTの場合はフォームから）
    selected_site_id = request.args.get("site_id", type=int)

    # 現在のユーザーのサイト一覧を取得
    sites = Site.query.filter_by(user_id=current_user.id).all()

    # サイトが1つも登録されていない場合はサイト追加ページにリダイレクト
    if not sites:
        return redirect(url_for("site.add_site"))

    # site_id が未指定なら最初のサイトを選択状態に
    if not selected_site_id:
        selected_site_id = sites[0].id

    # 総記事数を取得
    total_posts = ScheduledPost.query.filter_by(user_id=current_user.id).count()

    # サイトごとの投稿数を集計
    post_counts = {
        site.id: ScheduledPost.query.filter_by(user_id=current_user.id, site_id=site.id).count()
        for site in sites
    }

    # テンプレートを描画
    return render_template(
        "dashboard.html",
        sites=sites,
        selected_site_id=selected_site_id,
        total_posts=total_posts,
        post_counts=post_counts
    )
