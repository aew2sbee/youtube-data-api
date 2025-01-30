import os
from googleapiclient.discovery import build
from datetime import datetime
from dotenv import load_dotenv
from pprint import pprint

# .envファイルの読み込み
load_dotenv()

# .envから環境変数を取得
API_KEY = os.getenv('YOUTUBE_API_KEY')  # APIキー
VIDEO_ID = os.getenv('VIDEO_ID')  # 動画ID

# YouTube APIのクライアントのセットアップ
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

def get_live_chat_id(api_key, video_id):
    """ 指定したビデオIDのライブチャットIDを取得する """
    youtube = build("youtube", "v3", developerKey=api_key)

    response = youtube.videos().list(
        part="liveStreamingDetails",
        id=video_id
    ).execute()

    items = response.get("items", [])
    if not items:
        print("ライブ動画が見つかりませんでした")
        return None

    live_chat_id = items[0]["liveStreamingDetails"].get("activeLiveChatId")
    if not live_chat_id:
        print("ライブチャットIDが見つかりませんでした")
        return None

    return live_chat_id

def get_live_chat_messages(api_key, live_chat_id):
    """ 指定したライブチャットIDのメッセージを取得する """
    youtube = build("youtube", "v3", developerKey=api_key)

    response = youtube.liveChatMessages().list(
        liveChatId=live_chat_id,
        part="snippet,authorDetails"
    ).execute()

    messages = []
    for item in response.get("items", []):
        author = item["authorDetails"]["displayName"]
        message = item["snippet"]["displayMessage"]
        messages.append(f"{author}: {message}")

    return messages

if __name__ == "__main__":
    live_chat_id = get_live_chat_id(API_KEY, VIDEO_ID)
    if live_chat_id:
        messages = get_live_chat_messages(API_KEY, live_chat_id)
        for msg in messages:
            print(msg)