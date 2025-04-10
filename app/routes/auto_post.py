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

def generate_and_save_articles(app, keywords, site_id, user_id, result_list):
    with app.app_context():
        try:
            site = Site.query.filter_by(id=site_id, user_id=user_id).first()
            if not site:
                result_list.append({"title": "-", "status": "❌", "message": "サイトが見つかりません"})
                return

            jst = pytz.timezone("Asia/Tokyo")
            now = datetime.now(jst).replace(hour=0, minute=0, second=0, microsecond=0)

            all_times = []
            for day_offset in range(30):
                day = now + timedelta(days=day_offset)
                num_posts = random.choices([1, 2, 3, 4, 5], weights=[1, 2, 4, 6, 2])[0]
                hours = random.sample(range(10, 21), k=min(num_posts, 11))
                for h in sorted(hours):
                    minute = random.randint(0, 59)
                    all_times.append(day.replace(hour=h, minute=minute))

            all_times_utc = [t.astimezone(pytz.utc) for t in all_times][:len(keywords)]

            for i, kw in enumerate(keywords):
                try:
                    # タイトル生成
                    title_prompt = f"""あなたはSEOとコンテンツマーケティングの専門家です。

入力されたキーワードを使って
WEBサイトのQ＆A記事コンテンツに使用する「記事タイトル」を10個考えてください。

記事タイトルには必ず入力されたキーワードを全て使ってください  
キーワードの順番は入れ替えないでください  
最後は「？」で締めてください

【キーワード】
{kw}
"""
                    title_response = client.chat.completions.create(
                        model="gpt-4-turbo",
                        messages=[{"role": "system", "content": "あなたはSEOタイトル作成の専門家です。"},
                                  {"role": "user", "content": title_prompt}],
                        temperature=0.7,
                        max_tokens=300
                    )
                    title = title_response.choices[0].message.content.strip().split("\n")[0]

                    # 本文生成
                    content_prompt = f"""あなたはSEOとコンテンツマーケティングの専門家です。

入力された「Q＆A記事のタイトル」に対しての回答記事を以下の###条件###に沿って書いてください。

###条件###
・問題提起 → 共感 → 解決策の構成で
・読者が悩んでいることに答える内容で
・hタグで見出しをつける
・文字数2500〜3500文字
・1行30文字前後、文章の島ごとに2行空ける
・親友に語るように。ただし敬語
・「あなた」と呼びかけ、「皆さん」は使わない

【タイトル】
{title}
"""
                    content_response = client.chat.completions.create(
                        model="gpt-4-turbo",
                        messages=[{"role": "system", "content": "あなたはSEO記事ライターです。"},
                                  {"role": "user", "content": content_prompt}],
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

                    # Pixabay画像検索
                    image_query_prompt = f"""以下の日本語タイトルに対して、
Pixabayで画像を探すのに最適な英語の2～3語の検索キーワードを生成してください。
抽象的すぎる単語（life, businessなど）は避けてください。

タイトル: {title}
"""
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
                        genre="",
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

                    result_list.append({
                        "title": title,
                        "status": "✅ 成功",
                        "message": f"{kw} の記事を保存しました"
                    })
                    time.sleep(10)
                except Exception as inner_e:
                    result_list.append({
                        "title": "-",
                        "status": "❌ 失敗",
                        "message": f"{kw} の記事生成に失敗しました: {inner_e}"
                    })

        except Exception as e:
            result_list.append({"title": "-", "status": "❌", "message": f"全体エラー: {e}"})

@auto_post_bp.route("/auto-post", methods=["GET", "POST"])
@login_required
def auto_post():
    sites = Site.query.filter_by(user_id=current_user.id).all()
    result = []  # 結果リストを用意

    if request.method == "POST":
        keyword_text = request.form.get("keywords")
        keywords = [kw.strip() for kw in keyword_text.splitlines() if kw.strip()]
        site_id = int(request.form.get("site_id"))

        # 🔁 記事生成をバックグラウンドで実行
        app = current_app._get_current_object()
        thread = threading.Thread(
            target=generate_and_save_articles,
            args=(app, keywords, site_id, current_user.id, result)  # 結果を渡す
        )
        thread.start()

        # ✅ 即リダイレクト：投稿ログページに進捗状況を表示
        return render_template("admin_log.html", posts=result, site_id=site_id)  # resultを渡して即表示

    return render_template("auto_post.html", sites=sites)
