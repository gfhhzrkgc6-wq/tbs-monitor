import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask

app = Flask(__name__)

# 設定
TARGET_URL = 'https://tickets.tbs.co.jp/asp/select.aspx?org=1A&lid=TBSHP2612'
LINE_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')

# 前回の状態を保持する変数
previous_stock_state = None

def send_line_notification(message):
    if not LINE_ACCESS_TOKEN or not LINE_USER_ID:
        print("LINEの設定が環境変数にありません:", message)
        return
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    payload = {
        'to': LINE_USER_ID,
        'messages': [{'type': 'text', 'text': message}]
    }
    
    try:
        response = requests.post('https://api.line.me/v2/bot/message/push', json=payload, headers=headers)
        if response.status_code == 200:
            print('LINE通知を送信しました')
        else:
            print('LINE通知の送信に失敗しました:', response.text)
    except Exception as e:
        print('LINE通知エラー:', str(e))

def check_tickets():
    global previous_stock_state
    try:
        print('チケットページを確認中...')
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # ページ全体のテキストから余計な空白を削ったものを「現在の状態」とする
        current_stock_state = ''.join(soup.get_text().split())
        
        if previous_stock_state is None:
            previous_stock_state = current_stock_state
            print('初回チェック完了。監視を開始します。')
        elif previous_stock_state != current_stock_state:
            print('在庫の変動を検知しました！')
            previous_stock_state = current_stock_state
            send_line_notification(f"【チケット監視】\nTBSチケットのページに変動がありました！\n確認してください:\n{TARGET_URL}")
        else:
            print('変動なし')
    except Exception as e:
        print('スクレイピングエラー:', str(e))

# バックグラウンドで5分（300秒）おきにチェックをループさせる関数
def background_checker():
    while True:
        check_tickets()
        time.sleep(300)

# Renderのスリープ対策用＆手動確認用のWebサーバー設定
@app.route('/')
def home():
    return 'TBS Ticket Checker (Python) is running!'

@app.route('/check')
def manual_check():
    check_tickets()
    return 'Manual check executed.'

if __name__ == '__main__':
    # 別スレッドで5分おきの定期チェックを開始
    t = threading.Thread(target=background_checker, daemon=True)
    t.start()
    
    # サーバー起動
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
