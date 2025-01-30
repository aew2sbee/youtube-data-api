import os
from googleapiclient.discovery import build
from datetime import datetime
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# .envから環境変数を取得
API_KEY = os.getenv('YOUTUBE_API_KEY')  # APIキー
LIVE_CHAT_ID = os.getenv('LIVE_CHAT_ID')  # ライブチャットID

# YouTube APIのクライアントのセットアップ
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

# コメントの取得
def get_comments(live_chat_id):
    comments = []
    next_page_token = None  # 最初はpageTokenなしでリクエスト

    while True:
        # リクエストパラメータの設定
        request_params = {
            "liveChatId": live_chat_id,
            "part": "snippet",
        }
        
        # 次ページがあればpageTokenを設定
        if next_page_token:
            request_params["pageToken"] = next_page_token

        try:
            # コメントを取得
            response = youtube.liveChatMessages().list(**request_params).execute()

            # デバッグ: レスポンス内容を表示
            print("Response:", response)

            # コメントを収集
            for item in response['items']:
                author_name = item['snippet']['authorDisplayName']
                message = item['snippet']['displayMessage']
                timestamp = item['snippet']['publishedAt']
                timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")

                comments.append({'author': author_name, 'message': message, 'timestamp': timestamp})

            # 次のページがあれば次のリクエストで使用
            next_page_token = response.get('nextPageToken')

            # 次のページがなければ終了
            if not next_page_token:
                break

        except Exception as e:
            print(f"Error occurred: {e}")
            break

    return comments

# 「開始」「終了」コメントのタイムスタンプ差分を集計
def calculate_time_differences(comments):
    start_time = None
    end_time = None
    time_differences = []

    for comment in comments:
        message = comment['message'].lower()
        timestamp = comment['timestamp']

        # 「開始」「終了」コメントを見つける
        if '開始' in message:
            start_time = timestamp
        elif '終了' in message and start_time:
            end_time = timestamp
            time_diff = (end_time - start_time).total_seconds()
            time_differences.append(time_diff)
            start_time = None  # 次のペアのために開始時刻をリセット

    return time_differences

# 実行
comments = get_comments(LIVE_CHAT_ID)
time_differences = calculate_time_differences(comments)

# 結果の表示
if time_differences:
    print(f"コメントの開始と終了のタイムスタンプ差分（秒）:")
    for diff in time_differences:
        print(f"{diff}秒")
else:
    print("開始と終了のペアが見つかりませんでした。")
