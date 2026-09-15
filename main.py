import hashlib
import os
import time
import requests
from playwright.sync_api import sync_playwright

# --- 設定情報 ---
TARGET_URL = "https://tickets.tbs.co.jp/asp/select.aspx?org=1A&lid=TBSHP2612"
CACHE_FILE = "previous_ticket_status.txt"
CHECK_INTERVAL_SECONDS = 300  # 5分（300秒）ごとにチェック

# LINE設定
LINE_USER_ID = "U75d432e9151b1fc2d5a00f735b67ffbe"
LINE_CHANNEL_ACCESS_TOKEN = "+lFxGZRYeg83rw3is7FZ53XbHF43Ml+IuF9CzvG57sLRyzELZLgZ62I9ISS9a3+ICgRuxA66OwmuTzKrAm8kCCo55G2Q+KHIhIdVMAGxvq94XvJtq+BPwnfZIF3vshgTvJVPVQOAubH7tg7QjLSMmwdB04t89/1O/w1cDnyilFU="


def send_line_notification(message):
    """LINE Messaging APIを使ってメッセージを送信"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    payload = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print("-> LINE通知を送信しました。")
    except Exception as e:
        print(f"LINE通知エラー: {e}")


def get_ticket_inventory():
    """Playwrightでセッションを毎回新しく張り直してページテキストを取得"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 毎回新しいブラウザセッション（Cookie等リセット）を作成
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)

            # ページのテキスト情報を取得
            content = page.locator("body").text_content()

            browser.close()
            return content.strip() if content else None

        except Exception as e:
            print(f"取得エラー（タイムアウト等）: {e}")
            browser.close()
            return None


def check_for_updates():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] チケットページを確認中...")
    current_text = get_ticket_inventory()

    if not current_text:
        print("データ取得失敗のためスキップします。")
        return

    # 取得したテキストのハッシュ値を生成
    current_hash = hashlib.md5(current_text.encode("utf-8")).hexdigest()

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            previous_hash = f.read()

        if current_hash != previous_hash:
            msg = f"【TBSチケット更新検知】\nサイトの情報（在庫や表示内容）が更新されました！\n\n{TARGET_URL}"
            print(msg)
            send_line_notification(msg)

            # キャッシュ（履歴）を更新
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                f.write(current_hash)
        else:
            print("更新なし（変化はありませんでした）")
    else:
        # 初回実行時：現在の状態を保存
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(current_hash)
        print("初回チェック完了（現在の状態を保存しました）")


if __name__ == "__main__":
    print("=== TBSチケット 監視プログラム開始（5分間隔） ===")
    send_line_notification("監視プログラムを開始しました！（5分間隔）")

    while True:
        check_for_updates()
        time.sleep(CHECK_INTERVAL_SECONDS)
