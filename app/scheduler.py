# 📁 ファイルパス: app/scheduler.py

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from app.extensions import db
from app.models import ScheduledPost
from app.utils.wordpress_post import post_to_wordpress

scheduler = BackgroundScheduler()
scheduler_app = None  # Flaskアプリとの連携用

def check_and_post():
    if scheduler_app is None:
        print("⚠️ scheduler_app is None。Flaskアプリとの連携に失敗しています。")
        return

    with scheduler_app.app_context():
        now = datetime.utcnow()

        # ✅ 今この時点で投稿予定時間を過ぎていて、まだ投稿されていない記事を1件ずつ取得
        posts = ScheduledPost.query.filter(
            ScheduledPost.scheduled_time <= now,
            ScheduledPost.posted == False
        ).order_by(ScheduledPost.scheduled_time.asc()).all()

        if not posts:
            print("🕐 投稿対象なし（スケジュール待ち）")
            return

        for post in posts:
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
                print(f"✅ 投稿成功: {post.title}")
            else:
                print(f"❌ 投稿失敗: {post.title} | エラー: {message}")

# ✅ スケジューラー起動：毎分チェック
scheduler.add_job(func=check_and_post, trigger="interval", minutes=1)
scheduler.start()

def init_scheduler(app):
    global scheduler_app
    scheduler_app = app
