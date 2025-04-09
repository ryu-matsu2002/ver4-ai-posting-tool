# 📁 ファイルパス: app/routes/admin_log.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import pytz

from app.models import ScheduledPost, Site
from app.extensions import db
from app.utils.wordpress_post import post_to_wordpress

admin_log_bp = Blueprint("admin_log", __name__)


# ✅ 投稿ログ：サイト単位で表示
@admin_log_bp.route("/admin/log/<int:site_id>")
@login_required
def admin_post_log(site_id):
    posts = ScheduledPost.query.filter_by(user_id=current_user.id, site_id=site_id) \
        .order_by(ScheduledPost.scheduled_time.asc()).all()
    return render_template("admin_log.html", posts=posts, site_id=site_id)


# ✅ 投稿削除
@admin_log_bp.route("/admin/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = ScheduledPost.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        flash("不正な操作です", "error")
        return redirect(url_for("dashboard.dashboard"))

    db.session.delete(post)
    db.session.commit()
    flash("✅ 投稿を削除しました", "success")
    return redirect(url_for("admin_log.admin_post_log", site_id=post.site_id))


# ✅ 投稿編集
@admin_log_bp.route("/admin/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = ScheduledPost.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        flash("権限がありません", "error")
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        post.title = request.form["title"]
        post.body = request.form["body"]

        try:
            # フォーマット: "YYYY-MM-DDTHH:MM"
            post.scheduled_time = datetime.strptime(request.form["scheduled_time"], "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("⚠️ 日付フォーマットが正しくありません", "error")
            return redirect(url_for("admin_log.edit_post", post_id=post.id))

        db.session.commit()
        flash("✅ 投稿を更新しました", "success")
        return redirect(url_for("admin_log.admin_post_log", site_id=post.site_id))

    return render_template("edit_post.html", post=post)


# ✅ 投稿プレビュー
@admin_log_bp.route("/admin/preview/<int:post_id>")
@login_required
def preview_post(post_id):
    post = ScheduledPost.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        flash("アクセスが許可されていません", "error")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("preview_post.html", post=post)


# ✅ 即時投稿
@admin_log_bp.route("/post-now/<int:post_id>", methods=["POST"])
@login_required
def post_now(post_id):
    post = ScheduledPost.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        flash("操作が許可されていません", "error")
        return redirect(url_for("dashboard.dashboard"))

    if post.posted:
        flash("⚠️ すでに投稿済みです", "info")
        return redirect(url_for("admin_log.admin_post_log", site_id=post.site_id))

    success, message = post_to_wordpress(
        site_url=post.site_url,
        username=post.username,
        app_password=post.app_password,
        title=post.title,
        content=post.body,
        image_url=post.featured_image
    )

    if success:
        post.posted = True
        db.session.commit()
        flash("✅ 即時投稿が完了しました", "success")
    else:
        flash(f"❌ 投稿に失敗しました: {message}", "error")

    return redirect(url_for("admin_log.admin_post_log", site_id=post.site_id))
