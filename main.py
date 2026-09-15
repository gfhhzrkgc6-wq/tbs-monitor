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
    print(f"LINE通知送信を試みます... UserID: {LINE_USER_ID[:5]}...", flush=True)
    if not LINE_ACCESS_TOKEN or not LINE_USER_ID:
        print("【エラー】LINEの設定が環境変数にありません", flush=True)
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
        print(f"LINE API レスポンスコード: {response.status_code}", flush=True)
        if response.status_code == 200:
            print('【成功】LINE通知を送信しました！', flush=True)
        else:
            print(f'【失敗】LINE通知の送信に失敗しました: {response.text}', flush=True)
    except Exception as e:
        print(f'【エラー】LINE通知例外発生: {str(e)}', flush=True)

def check_tickets():
    global previous_stock_state
    try:
        print('チケットページを確認中...', flush=True)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        current_stock_state = ''.join(soup.get_text().split())
        
        if previous_stock_state is None:
            previous_stock_state = current_stock_state
            print('初回チェック完了。基準の状態を記憶しました。', flush=True)
            # テスト用に初回でも強制通知を送りたい場合は、下の行のコメントアウトを外せます
            # send_line_notification("【テスト】チケット監視ボットが起動しました！")
        elif previous_stock_state != current_stock_state:
            print('【検知】在庫の変動を検知しました！', flush=True)
            previous_stock_state = current_stock_state
            send_line_notification(f"【チケット監視】\nTBSチケットのページに変動がありました！\n確認してください:\n{TARGET_URL}")
        else:
            print('変動なし', flush=True)
    except Exception as e:
        print(f'【エラー】スクレイピングエラー: {str(e)}', flush=True)

def background_checker():
    while True:
        check_tickets()
        time.sleep(300)

@app.route('/')
def home():
    return 'TBS Ticket Checker (Python) is running!'

@app.route('/check')
def manual_check():
    print("手動チェック(/check)が呼び出されました", flush=True)
    check_tickets()
    return 'Manual check executed.'

if __name__ == '__main__':
    t = threading.Thread(target=background_checker, daemon=True)
    t.start()
    
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
