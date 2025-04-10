import os

# 本番環境以外でのみ .env を読み込む
if os.environ.get("FLASK_ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret")

    # データベースURLを直接設定（RenderのPostgreSQL接続情報）
    db_url = "postgresql://ver4_ai_posting_db_user:rziTchOqVC1gS6ATZQ69Jw7sMr8mls2B@dpg-cvr280be5dus73835760-a.singapore-postgres.render.com:5432/ver4_ai_posting_db?sslmode=require"
    
    # もし環境変数を使用する場合、以下のように設定することもできます
    # db_url = os.getenv("DATABASE_URL", "postgresql://ver4_ai_posting_db_user:rziTchOqVC1gS6ATZQ69Jw7sMr8mls2B@dpg-cvr280be5dus73835760-a.singapore-postgres.render.com:5432/ver4_ai_posting_db?sslmode=require")

    # もし DATABASE_URL 環境変数が不正なら、デフォルト値として設定
    if db_url and "sslmode" not in db_url:
        db_url += "?sslmode=require"  # SSL接続を強制

    # SQLAlchemy設定
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
