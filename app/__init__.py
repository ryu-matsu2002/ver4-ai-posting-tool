from flask import Flask, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.extensions import db
from app.models import User

def create_app():
    app = Flask(__name__)

    # Moment (タイムゾーンや日付フォーマット) 設定
    moment = Moment(app)  # MomentインスタンスをFlaskアプリにバインド

    # MomentフィルターをJinja2に追加
    @app.template_filter('moment')
    def moment_filter(dt, format='YYYY-MM-DD HH:mm'):
        return moment.date(dt).format(format)

    # アプリケーション設定
    app.config.from_object("config.Config")

    # DBとマイグレーションの設定
    db.init_app(app)

    # ログイン設定
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # ログインが必要なページの設定

    # user_loaderの設定
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ホームルート設定（ログイン後にダッシュボードにリダイレクト）
    @app.route("/")
    def home():
        return redirect(url_for("dashboard_bp.dashboard"))

    # デバッグモードを有効にする
    app.debug = True

    return app
