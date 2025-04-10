from flask import Flask, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.extensions import db
from app.models import User
from app.routes.dashboard import dashboard_bp  # 修正：app.dashboardからapp.routes.dashboardに変更
from app.routes.site import site_bp  # 修正：app.siteからapp.routes.siteに変更

def create_app():
    app = Flask(__name__)

    # Moment (タイムゾーンや日付フォーマット) 設定
    moment = Moment(app)

    # アプリケーション設定
    app.config.from_object("config.Config")

    # DBとマイグレーションの設定
    db.init_app(app)

    # ログイン設定
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # user_loaderの設定
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprintの登録
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')  # dashboard Blueprintを登録
    app.register_blueprint(site_bp, url_prefix='/site')  # site Blueprintを登録

    # ホームルート設定（ログイン後にダッシュボードにリダイレクト）
    @app.route("/")
    def home():
        return redirect(url_for("dashboard.dashboard"))  # 修正されたエンドポイント名

    return app
