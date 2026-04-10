#!/usr/bin/env python3
# pop grumpy #オーダーペイント ギャラリー生成スクリプト
# posts.json を読み込んで index.html を生成する

import json, os, sys

# posts.json のパスを決定（スクリプトと同じディレクトリ）
script_dir = os.path.dirname(os.path.abspath(__file__))
posts_json_path = os.path.join(script_dir, 'posts.json')

with open(posts_json_path, encoding='utf-8') as f:
    data = json.load(f)

posts_by_category = {cat: posts for cat, posts in data['posts_by_category'].items()}
last_updated = data['meta'].get('last_updated', '')

# カラースウォッチ
category_dot = {
  "ホワイト・クリーム系":   "#E8DDD0",
  "ブラック系":             "#2A2A2A",
  "グレー・シルバー系":     "#9A9A9A",
  "ネイビー・ブルー系":     "#2E5D9C",
  "レッド・オレンジ系":     "#C0392B",
  "グリーン系":             "#2E6B42",
  "イエロー・マスタード系": "#C8980A",
  "ベージュ・ブラウン系":   "#9A7550",
  "その他":                 "#AAAAAA",
}

# Decode shortcode → media ID for chronological sort
B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
def shortcode_to_id(s):
    n = 0
    for c in s:
        if c in B64:
            n = n * 64 + B64.index(c)
    return n

# Flatten & deduplicate (first category wins)
all_posts = []
seen = set()
for cat, posts in posts_by_category.items():
    for item in posts:
        code, color_name = item[0], item[1]
        if code not in seen:
            seen.add(code)
            all_posts.append({"code": code, "color_name": color_name, "cat": cat})

all_posts.sort(key=lambda p: shortcode_to_id(p["code"]), reverse=True)
total = len(all_posts)
categories = list(posts_by_category.keys())

# カテゴリごとのユニーク件数
cat_counts = {}
for p in all_posts:
    cat_counts[p["cat"]] = cat_counts.get(p["cat"], 0) + 1

def gen_filters():
    btns = f'<button class="filter active" data-cat="all">すべて <span class="fcount">({total})</span></button>\n'
    for cat in categories:
        if cat not in cat_counts:
            continue
        dot = category_dot.get(cat, "#888")
        cnt = cat_counts[cat]
        border = "border:1.5px solid #ccc;" if dot == "#E8DDD0" else ""
        btns += f'<button class="filter" data-cat="{cat}"><span class="dot" style="background:{dot};{border}"></span>{cat} <span class="fcount">({cnt})</span></button>\n'
    return btns

def gen_cards():
    cards = ""
    for p in all_posts:
        code = p["code"]
        color_name = p["color_name"]
        cat = p["cat"]
        is_matte = any(k in color_name for k in ["マット","パウダー"]) if color_name else False
        matte_badge = '<span class="matte-badge">MATTE</span>' if is_matte else ""
        display_name = color_name if color_name and color_name != "（色指定なし）" else "カラー未記載"
        dot = category_dot.get(cat, "#888")
        border = "border:1px solid #ddd;" if dot == "#E8DDD0" else ""
        cards += f'''
        <div class="card" data-cat="{cat}">
          <div class="embed-wrap">
            {matte_badge}
            <iframe src="https://www.instagram.com/p/{code}/embed/"
              frameborder="0" scrolling="no" allowtransparency="true"
              loading="lazy" title="{display_name}"></iframe>
            <a href="https://www.instagram.com/p/{code}/" class="embed-link" target="_self" aria-label="{display_name}"></a>
          </div>
          <div class="card-foot">
            <span class="card-color"><span class="dot-sm" style="background:{dot};{border}"></span>{display_name}</span>
            <a href="https://www.instagram.com/p/{code}/" class="ig-link">Instagram ↗</a>
          </div>
        </div>'''
    return cards

html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>pop grumpy | #オーダーペイント カラーギャラリー</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Helvetica,Arial,sans-serif;font-size:15px;background:#fff;color:#3a3a3a;min-height:100vh}}
.site-header{{background:#fff;border-bottom:1px solid #ebebeb;padding:20px 28px 16px;position:sticky;top:0;z-index:200}}
.site-header h1{{font-size:1rem;font-weight:600;color:#3a3a3a;letter-spacing:.04em;text-transform:uppercase}}
.site-header p{{font-size:.72rem;color:#aaa;margin-top:4px;letter-spacing:.02em}}
.filters{{display:flex;flex-wrap:wrap;gap:6px;padding:12px 28px;background:#fff;border-bottom:1px solid #ebebeb;position:sticky;top:65px;z-index:199}}
.filter{{display:inline-flex;align-items:center;gap:6px;padding:5px 13px;border-radius:20px;border:1.5px solid #ebebeb;background:#fff;color:#3a3a3a;font-family:Helvetica,Arial,sans-serif;font-size:.72rem;font-weight:500;cursor:pointer;white-space:nowrap;transition:border-color .15s,background .15s;letter-spacing:.02em}}
.filter:hover{{border-color:#ccc}}
.filter.active{{background:#3a3a3a;color:#fff;border-color:#3a3a3a}}
.filter.active .fcount{{color:rgba(255,255,255,.65)}}
.fcount{{color:#aaa;font-size:.68rem}}
.dot{{display:inline-block;width:9px;height:9px;border-radius:50%;flex-shrink:0}}
main{{padding:28px;max-width:1440px;margin:0 auto}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(285px,1fr));gap:16px}}
.card{{background:#fff;border:1px solid #ebebeb;border-radius:6px;overflow:hidden;display:flex;flex-direction:column;transition:box-shadow .2s}}
.card:hover{{box-shadow:0 4px 20px rgba(0,0,0,.09)}}
.card.hidden{{display:none}}
.embed-wrap{{position:relative;width:100%;height:430px;overflow:hidden;background:#f7f7f7}}
.embed-wrap iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:none;z-index:2;background:transparent}}
.embed-link{{position:absolute;top:0;left:40px;width:calc(100% - 80px);height:100%;z-index:3;display:block;text-decoration:none;background:transparent}}
.matte-badge{{position:absolute;top:8px;right:8px;z-index:4;background:rgba(58,58,58,.6);color:#fff;font-size:.58rem;font-weight:700;padding:2px 7px;border-radius:10px;letter-spacing:.07em;text-transform:uppercase}}
.card-foot{{padding:9px 12px;border-top:1px solid #ebebeb;display:flex;align-items:center;justify-content:space-between;gap:8px}}
.card-color{{display:flex;align-items:center;gap:5px;font-size:.72rem;color:#3a3a3a;font-weight:500;min-width:0;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}}
.dot-sm{{display:inline-block;width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.ig-link{{font-size:.68rem;color:#aaa;text-decoration:none;white-space:nowrap;flex-shrink:0;transition:color .15s}}
.ig-link:hover{{color:rgb(242,144,107)}}
.empty{{display:none;grid-column:1/-1;text-align:center;padding:60px 20px;color:#ccc;font-size:.85rem;letter-spacing:.04em}}
footer{{text-align:center;padding:32px 20px;color:#ccc;font-size:.68rem;border-top:1px solid #ebebeb;line-height:2;letter-spacing:.03em;margin-top:20px}}
@media(max-width:600px){{
  .site-header{{padding:14px 16px 12px}}
  .site-header h1{{font-size:.88rem}}
  .filters{{padding:10px 16px;top:57px}}
  main{{padding:16px}}
  .grid{{grid-template-columns:1fr;gap:12px}}
}}
</style>
</head>
<body>
<header class="site-header">
  <h1>pop grumpy — Order Paint Gallery</h1>
  <p>#オーダーペイント アーカイブ &nbsp;|&nbsp; {total} 件 &nbsp;|&nbsp; 更新: {last_updated}</p>
</header>
<nav class="filters">
{gen_filters()}
</nav>
<main>
  <div class="grid" id="grid">
{gen_cards()}
    <div class="empty" id="empty">該当する投稿がありません</div>
  </div>
</main>
<footer>
  <p>pop grumpy（@popgrumpy）の #オーダーペイント 投稿を色別に整理したカラーギャラリーです。</p>
  <p>画像・投稿はすべて Instagram および @popgrumpy に帰属します。</p>
</footer>
<script>
(function(){{
  var btns = document.querySelectorAll('.filter');
  var cards = document.querySelectorAll('.card');
  var empty = document.getElementById('empty');
  function filter(cat) {{
    var v = 0;
    cards.forEach(function(c) {{
      var show = cat==='all' || c.dataset.cat===cat;
      c.classList.toggle('hidden',!show);
      if(show) v++;
    }});
    empty.style.display = v===0 ? 'block' : 'none';
  }}
  btns.forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      btns.forEach(function(b){{ b.classList.remove('active'); }});
      btn.classList.add('active');
      filter(btn.dataset.cat);
      window.scrollTo({{top:0,behavior:'smooth'}});
    }});
  }});
}})();
</script>
</body>
</html>'''

out = os.path.join(script_dir, 'index.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ {out}")
print(f"   合計: {total}件 / 更新日: {last_updated}")
for cat in categories:
    if cat in cat_counts:
        print(f"   {cat}: {cat_counts[cat]}件")
