# app/routes/dashboard.py
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.models import ScheduledPost, Site

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    selected_site_id = request.args.get("site_id", type=int)
    sites = Site.query.filter_by(user_id=current_user.id).all()

    if not sites:
        return redirect(url_for("site.add_site"))

    if not selected_site_id:
        selected_site_id = sites[0].id

    total_posts = ScheduledPost.query.filter_by(user_id=current_user.id).count()
    post_counts = {
        site.id: ScheduledPost.query.filter_by(user_id=current_user.id, site_id=site.id).count()
        for site in sites
    }

    return render_template(
        "dashboard.html",
        sites=sites,
        selected_site_id=selected_site_id,
        total_posts=total_posts,
        post_counts=post_counts
    )
