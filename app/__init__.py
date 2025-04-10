from flask import Flask
from flask_moment import Moment
from app.models import User
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.extensions import db

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

    return app
