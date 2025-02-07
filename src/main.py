import os
from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from pprint import pprint
import json

# 現在の日付と時刻を取得（JST 日本時間に変換）
now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=9)))
current_time_str = now.strftime("%Y/%m/%d")  # YYYY/MM/DD フォーマット

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

def convert_utc_to_jst(timestamp):
    # タイムスタンプを UTC からローカル時刻に変換
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    local_time = dt.astimezone(timezone(timedelta(hours=9)))  # JST に変換
    return local_time

def get_live_chat_messages(api_key, live_chat_id):
    """ 指定したライブチャットIDのメッセージを取得し、開始/終了の差分を集計する """
    youtube = build("youtube", "v3", developerKey=api_key)

    response = youtube.liveChatMessages().list(
        liveChatId=live_chat_id,
        part="snippet,authorDetails"
    ).execute()

    user_timestamps = {}  # ユーザーごとの「開始」時刻を記録
    user_durations = {}  # ユーザーごとの滞在時間を集計

    for item in response.get("items", []):
        author = item["authorDetails"]["displayName"]
        message = item["snippet"]["displayMessage"]
        timestamp = convert_utc_to_jst(item["snippet"]["publishedAt"])

        # 「開始」メッセージを記録
        if "開始" in message:
            user_timestamps[author] = timestamp
        # 「終了」メッセージを検出して差分を計算
        if "終了" in message and author in user_timestamps:
            start_time = user_timestamps.pop(author)  # 「開始」時刻を取得して削除
            duration = (timestamp - start_time).total_seconds()  # 差分を秒単位で計算

            # ユーザーごとの合計時間を集計
            if author in user_durations:
                user_durations[author] += duration
            else:
                user_durations[author] = duration

    return user_durations

def load_previous_month_data():
    """ output/jsonディレクトリ内の全てのJSONファイルを読み込み、累計時間を計算 """
    current_month = now.strftime("%Y-%m")  # 現在の月（YYYY-MM）
    previous_month_data = {}

    # output/jsonディレクトリ内の全てのJSONファイルを読み込む
    json_files = [f for f in os.listdir('./output/json') if f.endswith('.json')]

    for json_file in json_files:
        file_path = f"./output/json/{json_file}"
        if current_month in json_file:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                for entry in data:
                    user = entry['user']
                    study_time_seconds = entry['study_time_seconds']
                    if user in previous_month_data:
                        previous_month_data[user] += study_time_seconds
                    else:
                        previous_month_data[user] = study_time_seconds

    return previous_month_data

def format_duration(seconds):
    """ 秒数を X時間Y分 に変換 (小数点なし) """
    hours = int(seconds // 3600)  # 時間
    minutes = int((seconds % 3600) // 60)  # 分
    if hours > 0:
        return f"{hours}時間{minutes}分"
    else:
        return f"{minutes}分"

def save_to_file(user_durations):
    """ 結果をファイルに保存 """
    current_date = now.strftime("%Y-%m-%d_%H-%M")  # 日付と時間（HH-MM）を追加

    # JSONファイル保存 (秒数で保存)
    json_filename = f"./output/json/{current_date}.json"
    json_data = [{"user": user, "study_time_seconds": duration} for user, duration in user_durations.items()]

    with open(json_filename, "w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=4)

    print(f"save: {json_filename}")

    # 前月の累計データを読み込む
    previous_month_data = load_previous_month_data()

    # 累計時間を加算
    for user, duration in user_durations.items():
        if user in previous_month_data:
            previous_month_data[user] += duration
        else:
            previous_month_data[user] = duration

    # テキストファイル保存
    txt_filename = f"./output/txt/{current_date}.txt"
    with open(txt_filename, "w", encoding="utf-8") as file:
        # 今月の勉強時間ランキングの表示
        file.write(f"🥇今月の勉強時間ランキング({current_time_str}時点)\n")

        # ユーザーごとの滞在時間を長い順にソート
        sorted_user_durations = sorted(previous_month_data.items(), key=lambda x: x[1], reverse=True)

        for rank, (user, duration) in enumerate(sorted_user_durations, start=1):
            # 今日の時間（user_durations）を計算
            today_duration = user_durations.get(user, 0)
            formatted_duration = format_duration(duration)
            today_formatted = format_duration(today_duration)

            # 出力形式に合わせて表示
            file.write(f"{rank}. {user}: {formatted_duration}(+{today_formatted})\n")

    print(f"save: {txt_filename}")

if __name__ == "__main__":
    live_chat_id = get_live_chat_id(API_KEY, VIDEO_ID)
    if live_chat_id:
        user_durations = get_live_chat_messages(API_KEY, live_chat_id)

        # 結果をファイルに保存
        if user_durations:
            save_to_file(user_durations)
        else:
            print("記録がありませんでした")
