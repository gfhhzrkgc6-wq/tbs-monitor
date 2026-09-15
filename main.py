import os
import time
import threading
import requests
import schedule
from flask import Flask
from bs4 import BeautifulSoup

# --- Renderの無料プラン（Web Service）対策の簡易サーバー ---
app = Flask(__name__)

@app.route('/')
def home():
    return "TBS Monitor is running!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def start_server_in_background():
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
# -------------------------------------------------------------

# LINE Notify トークン（環境変数から取得）
LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN")
# TBSチケットの監視対象URL
TARGET_URL = "https://tickets.tbs.co.jp/"  

def send_line_notify(message):
    if not LINE_NOTIFY_TOKEN:
        print("LINE_NOTIFY_TOKEN が設定されていません")
        return
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"}
    data = {"message": message}
    requests.post(url, headers=headers, data=data)

def check_website():
    print("TBSチケットの監視チェックを開始します...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(TARGET_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else "タイトルなし"
        
        print(f"取得タイトル: {title}")
        send_line_notify(f"\n【TBS定期チェック】\nサイトの確認が完了しました！\nタイトル: {title}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        send_line_notify(f"\n【エラー発生】\nTBS監視処理中にエラーが発生しました:\n{e}")

if __name__ == "__main__":
    start_server_in_background()

    # 毎時 05 分に実行するスケジュール設定
    schedule.every().hour.at(":05").do(check_website)

    print("TBS監視プログラムを起動しました。毎時05分に実行します...")

    check_website()

    while True:
        schedule.run_pending()
        time.sleep(30)
