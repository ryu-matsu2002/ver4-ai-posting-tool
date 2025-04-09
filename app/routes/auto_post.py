import os
import threading
import time
import random
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from flask_login import current_user, login_required
from dotenv import load_dotenv
from openai import OpenAI
import pytz

from app.extensions import db
from app.models import ScheduledPost, Site
from app.utils.image_search import search_pixabay_images

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
auto_post_bp = Blueprint("auto_post", __name__)

def generate_and_save_articles(app, keywords, site_id, user_id):
    with app.app_context():
        try:
            site = Site.query.filter_by(id=site_id, user_id=user_id).first()
            if not site:
                return

            jst = pytz.timezone("Asia/Tokyo")
            now = datetime.now(jst).replace(hour=0, minute=0, second=0, microsecond=0)

            # 🔹 1ヶ月分のスケジュールを生成（1日1〜5記事、平均4記事で計120記事）
            all_times = []
            for day_offset in range(30):
                day = now + timedelta(days=day_offset)
                num_posts = random.choices([1, 2, 3, 4, 5], weights=[1, 2, 3, 5, 2])[0]  # 平均4記事
                hours = random.sample(range(6, 23), num_posts)  # 6〜22時
                for h in sorted(hours):
                    minute = random.choice([0, 10, 20, 30, 40, 50])
                    all_times.append(day.replace(hour=h, minute=minute))

            # 🔹 時刻をUTCに変換して上から使う（最大120件）
            all_times_utc = [t.astimezone(pytz.utc) for t in all_times][:len(keywords)]

            for i, kw in enumerate(keywords):
                title_prompt = f"""あなたはSEOとコンテンツマーケティングの専門家です。

入力されたキーワードを使って
WEBサイトのQ＆A記事コンテンツに使用する「記事タイトル」を10個考えてください。

記事タイトルには必ず入力されたキーワードを全て使ってください  
キーワードの順番は入れ替えないでください  
最後は「？」で締めてください

【キーワード】
{kw}

###具体例###

「転職 時期」というキーワードに対する出力文：  
転職に有利な時期があるって本当ですか？

「転職 面接 聞かれること」というキーワードに対する出力文：  
転職面接で必ず聞かれることとは？
"""
                title_response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "あなたはSEOタイトル作成の専門家です。"},
                        {"role": "user", "content": title_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                title = title_response.choices[0].message.content.strip().split("\n")[0]

                content_prompt = f"""あなたはSEOとコンテンツマーケティングの専門家です。

入力された「Q＆A記事のタイトル」に対しての回答記事を以下の###条件###に沿って書いてください。

###条件###
・文章の構成としては、問題提起、共感、問題解決策の順で書いてください。
・Q＆A記事のタイトルについて悩んでいる人が知りたい事を書いてください。
・見出し（hタグ）を付けてわかりやすく書いてください
・記事の文字数は必ず2500文字〜3500文字程度でまとめてください
・1行の長さは30文字前後にして接続詞などで改行してください。
・「文章の島」は1行から3行以内にして、文章の島同士は2行空けてください
・親友に向けて話すように書いてください（ただし敬語を使ってください）
・読み手のことは「皆さん」ではなく必ず「あなた」と書いてください。

【タイトル】
{title}"""
                content_response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "あなたはSEO記事ライターです。"},
                        {"role": "user", "content": content_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=3000
                )
                raw_text = content_response.choices[0].message.content.strip()

                html_lines = []
                for block in raw_text.split("\n\n"):
                    block = block.strip()
                    if block.startswith("###"):
                        html_lines.append(f"<h2>{block.lstrip('# ').strip()}</h2>")
                    elif block:
                        html_lines.append(f"<p>{block}</p>")

                image_query_prompt = f"""以下の日本語タイトルに対して、
Pixabayで画像を探すのに最適な英語の2～3語の検索キーワードを生成してください。
抽象的すぎる単語（life, business など）は避けてください。
写真としてヒットしやすい「モノ・場所・情景・体験・風景」などを選んでください。

タイトル: {title}"""
                image_query_response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "あなたはPixabay用の画像検索キーワード生成の専門家です。"},
                        {"role": "user", "content": image_query_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=50
                )
                image_query = image_query_response.choices[0].message.content.strip()
                image_urls = search_pixabay_images(image_query, max_images=2)

                final_html = []
                image_index = 0
                for j, line in enumerate(html_lines):
                    if line.startswith("<h2>") and j > 0 and image_index < len(image_urls):
                        final_html.append(f'<img src="{image_urls[image_index]}" style="max-width:100%; margin: 20px 0;">')
                        image_index += 1
                    final_html.append(line)

                scheduled_post = ScheduledPost(
                    genre="",  # ジャンル不要にした場合は空欄
                    keyword=kw,
                    title=title,
                    body="\n".join(final_html),
                    featured_image=image_urls[0] if image_urls else None,
                    site_url=site.url,
                    username=site.username,
                    app_password=site.app_password,
                    scheduled_time=all_times_utc[i],
                    user_id=user_id,
                    site_id=site.id
                )
                db.session.add(scheduled_post)
                db.session.commit()
                time.sleep(10)
        except Exception as e:
            print(f"エラー: {e}")

@auto_post_bp.route("/auto-post", methods=["GET", "POST"])
@login_required
def auto_post():
    sites = Site.query.filter_by(user_id=current_user.id).all()
    if request.method == "POST":
        keyword_text = request.form.get("keywords")
        keywords = [kw.strip() for kw in keyword_text.splitlines() if kw.strip()]
        site_id = int(request.form.get("site_id"))

        app = current_app._get_current_object()
        thread = threading.Thread(target=generate_and_save_articles, args=(app, keywords, site_id, current_user.id))
        thread.start()

        return redirect(url_for("admin_log.admin_post_log", site_id=site_id))

    return render_template("auto_post.html", sites=sites)
