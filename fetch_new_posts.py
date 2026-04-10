#!/usr/bin/env python3
"""
fetch_new_posts.py
Instagram の popgrumpy フィードを巡回し、
「オーダーペイント」を含む新規投稿を posts.json に追記するスクリプト。

必要環境変数:
  INSTAGRAM_SESSION_ID  ... Instagram の sessionid cookie 値（GitHub Secret）

使い方:
  python3 fetch_new_posts.py
  終了コード 0 = 変更なし / 1 = 新規投稿あり（posts.json + index.html を更新済み）
"""

import json, os, re, sys, time, subprocess
from datetime import date

# ── 設定 ──────────────────────────────────────────────────────────────────────
USER_ID   = "5377540779"      # @popgrumpy の数値 ID
KEYWORD   = "オーダーペイント"
MAX_PAGES = 10                # 1回の実行で最大何ページまでチェックするか（1ページ12件）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_JSON = os.path.join(SCRIPT_DIR, "posts.json")

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# ── 色カテゴリ判定 ──────────────────────────────────────────────────────────
COLOR_PATTERNS = [
    ("ホワイト・クリーム系",   r"ホワイト|白|クリーム|ミルキー|オフホワイト|アイボリー|オートミール"),
    ("ブラック系",             r"ブラック|黒|マットブラック|クリアブラック|Rawフィニッシュ"),
    ("グレー・シルバー系",     r"グレー|シルバー|RAWカラー|グラファイト|ラットグレー|ダークシルバー"),
    ("ネイビー・ブルー系",     r"ネイビー|ブルー|青|ピジョン|ICE BLUE|アイスブルー"),
    ("レッド・オレンジ系",     r"レッド|赤|オレンジ|コーラル|フラッシュレッド"),
    ("グリーン系",             r"グリーン|緑|モス|ミント|裏葉柳|ブラスグリーン|ダークグリーン"),
    ("イエロー・マスタード系", r"イエロー|黄|マスタード|サフラン|レモン"),
    ("ベージュ・ブラウン系",   r"ベージュ|ブラウン|茶|パール.*ベージュ|一升瓶"),
]

def guess_category(caption: str) -> tuple[str, str]:
    """キャプションからカテゴリと色名を推定する"""
    for cat, pattern in COLOR_PATTERNS:
        m = re.search(pattern, caption)
        if m:
            start = max(0, m.start() - 5)
            end   = min(len(caption), m.end() + 10)
            color_snippet = caption[start:end].strip()
            color_snippet = re.sub(r'[\n\r#@\[\]【】「」]', ' ', color_snippet).strip()
            color_snippet = re.sub(r'\s+', ' ', color_snippet)[:40]
            return cat, color_snippet
    return "その他", "（色指定なし）"

# ── B64 shortcode ↔ ID 変換 ──────────────────────────────────────────────────
B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
def id_to_shortcode(media_id: int) -> str:
    s = ""
    while media_id > 0:
        s = B64[media_id % 64] + s
        media_id //= 64
    return s

# ── Instagram API ────────────────────────────────────────────────────────────
SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID", "")
if not SESSION_ID:
    print("⚠️  INSTAGRAM_SESSION_ID が設定されていません。スキップします。")
    sys.exit(0)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "X-IG-App-ID": "936619743392459",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.instagram.com/",
    "Cookie": f"sessionid={SESSION_ID}; ds_user_id={USER_ID};",
}

def fetch_feed_page(cursor: str = "") -> dict:
    url = f"https://www.instagram.com/api/v1/feed/user/{USER_ID}/?count=12"
    if cursor:
        url += f"&max_id={cursor}"
    resp = requests.get(url, headers=HEADERS, timeout=20)
    if resp.status_code != 200:
        print(f"  API エラー: {resp.status_code}")
        return {}
    return resp.json()

# ── メイン処理 ───────────────────────────────────────────────────────────────
def main():
    with open(POSTS_JSON, encoding="utf-8") as f:
        data = json.load(f)

    existing_codes = set()
    for posts in data["posts_by_category"].values():
        for item in posts:
            existing_codes.add(item[0])

    newest_existing_id = max(
        (sum(B64.index(c) * (64 ** i) for i, c in enumerate(reversed(code)))
         for code in existing_codes if all(c in B64 for c in code)),
        default=0
    )

    print(f"📋 既存投稿数: {len(existing_codes)}件")
    print(f"🔍 Instagram をチェック中... (最大 {MAX_PAGES} ページ)")

    new_posts = []
    cursor = ""
    stop = False

    for page in range(MAX_PAGES):
        time.sleep(1.5)
        result = fetch_feed_page(cursor)
        if not result:
            break

        items = result.get("items", [])
        if not items:
            break

        for item in items:
            media_id = int(item.get("pk", 0) or item.get("id", "0").split("_")[0])
            code     = id_to_shortcode(media_id)
            media_type = item.get("media_type", 1)

            if media_type == 2:
                continue

            if media_id <= newest_existing_id and page > 0:
                stop = True
                break

            cap_node = item.get("caption") or {}
            caption  = cap_node.get("text", "") if isinstance(cap_node, dict) else ""

            if KEYWORD not in caption:
                continue

            if code not in existing_codes:
                cat, color_name = guess_category(caption)
                new_posts.append({"code": code, "color_name": color_name, "cat": cat})
                print(f"  ✨ 新規: {code} [{cat}] {color_name[:30]}")

        if stop:
            break

        cursor = result.get("next_max_id", "")
        if not cursor:
            break

        print(f"  ページ {page+1} 完了 ({len(items)}件チェック)")

    if not new_posts:
        print("✅ 新規投稿なし。更新不要です。")
        sys.exit(0)

    today = str(date.today())
    for post in new_posts:
        cat = post["cat"]
        if cat not in data["posts_by_category"]:
            data["posts_by_category"][cat] = []
        data["posts_by_category"][cat].insert(0, [post["code"], post["color_name"]])

    data["meta"]["last_updated"] = today

    with open(POSTS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n📝 posts.json を更新しました ({len(new_posts)}件追加)")

    gen_script = os.path.join(SCRIPT_DIR, "generate_gallery.py")
    subprocess.check_call([sys.executable, gen_script])

    sys.exit(1)

if __name__ == "__main__":
    main()
