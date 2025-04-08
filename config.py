import os

# 本番環境以外でのみ .env を読み込む
if os.environ.get("FLASK_ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret")

    # DATABASE_URL の形式が postgres:// の場合 → SQLAlchemy 用に postgresql:// に修正
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # ✅ Render用にSSLモード強制追加
    if db_url and "sslmode" not in db_url:
        db_url += "?sslmode=require"

    # ✅ デフォルトは /tmp にSQLite（Render環境向け）
    if not db_url:
        sqlite_path = os.path.join("/tmp", "app.db")
        db_url = f"sqlite:///{sqlite_path}"

    SQLALCHEMY_DATABASE_URI = db_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False
