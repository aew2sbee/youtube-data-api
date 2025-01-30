import os
from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# 現在の日付と時刻を取得（JST 日本時間に変換）
now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=9)))
current_time_str = now.strftime("%Y/%m/%d")  # YYYY/MM/DD フォーマット
current_date = now.strftime("%Y-%m-%d_%H-%M")  # 日付と時間（HH-MM）を追加

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

def format_duration(seconds):
    """ 秒数を X時間Y分 に変換 """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}時間{minutes}分"
    else:
        return f"{minutes}分"

def get_live_chat_messages(api_key, live_chat_id):
    """ 指定したライブチャットIDのメッセージを取得し、開始/終了の差分を集計する """
    youtube = build("youtube", "v3", developerKey=api_key)

    response = youtube.liveChatMessages().list(
        liveChatId=live_chat_id,
        part="snippet,authorDetails"
    ).execute()

    messages = []
    user_timestamps = {}  # ユーザーごとの「開始」時刻を記録
    user_durations = {}  # ユーザーごとの滞在時間を集計

    for item in response.get("items", []):
        author = item["authorDetails"]["displayName"]
        message = item["snippet"]["displayMessage"]
        timestamp = item["snippet"]["publishedAt"]

        # タイムスタンプを UTC からローカル時刻に変換
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        local_time = dt.astimezone(timezone.utc)  # 必要に応じて JST などに変換

        messages.append(f"[{local_time.strftime('%Y-%m-%d %H:%M:%S')}] {author}: {message}")

        # 「開始」メッセージを記録
        if "開始" in message:
            user_timestamps[author] = local_time

        # 「終了」メッセージを検出して差分を計算
        if "終了" in message and author in user_timestamps:
            start_time = user_timestamps.pop(author)  # 「開始」時刻を取得して削除
            duration = (local_time - start_time).total_seconds()  # 差分を秒単位で計算

            # ユーザーごとの合計時間を集計
            if author in user_durations:
                user_durations[author] += duration
            else:
                user_durations[author] = duration

    return messages, user_durations

def save_to_file(messages, user_durations, current_date):
    """ 結果をファイルに保存 """
    filename = f"./output/{current_date}.txt"
    with open(filename, "w", encoding="utf-8") as file:
        # 今月の勉強時間ランキングの表示
        file.write(f"\n🥇 今月の勉強時間ランキング({current_time_str}時点)\n")

        # ユーザーごとの滞在時間を長い順にソート
        sorted_user_durations = sorted(user_durations.items(), key=lambda x: x[1], reverse=True)

        for rank, (user, duration) in enumerate(sorted_user_durations, start=1):
            file.write(f"{rank}. {user}: {format_duration(duration)}.\n")

    print(f"結果を {filename} に保存しました！")

if __name__ == "__main__":
    live_chat_id = get_live_chat_id(API_KEY, VIDEO_ID)
    if live_chat_id:
        messages, user_durations = get_live_chat_messages(API_KEY, live_chat_id)

        # 結果をファイルに保存
        save_to_file(messages, user_durations, current_date)
