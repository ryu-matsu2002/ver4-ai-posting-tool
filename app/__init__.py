from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment  # ← Momentをインポート

from app.routes.article import article_bp
from app.routes.title import title_bp
from app.routes.keyword import keyword_bp
from app.routes.post_test import post_test_bp
from app.routes.dashboard import dashboard_bp
from app.routes.auto_post import auto_post_bp
from app.routes.admin_log import admin_log_bp
from app.routes.auth import auth_bp  # ← 追加: 認証関連
from app.routes.site import site_bp  # ← 追加: サイト関連
from app.extensions import db

from app.models import User
from app.scheduler import init_scheduler

# Flask-Login 設定
login_manager = LoginManager()
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)

    # Moment (タイムゾーンや日付フォーマット) 設定
    moment = Moment(app)  # ← MomentインスタンスをFlaskアプリにバインド

    # アプリケーション設定
    app.config.from_object("config.Config")

    # DBとマイグレーションの設定
    migrate = Migrate(app, db)

    # DB初期化
    db.init_app(app)

    # ログイン設定
    login_manager.init_app(app)

    # スケジューラ設定（もしあれば）
    init_scheduler(app)

    # Blueprints 登録
    app.register_blueprint(article_bp)
    app.register_blueprint(title_bp)
    app.register_blueprint(keyword_bp)
    app.register_blueprint(post_test_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auto_post_bp)
    app.register_blueprint(admin_log_bp)
    app.register_blueprint(auth_bp)  # ← 認証Blueprintを登録
    app.register_blueprint(site_bp)  # ← サイト管理Blueprintを登録

    # ホームルートの設定
    @app.route("/")
    def home():
        return redirect(url_for("dashboard.dashboard"))

    return app
