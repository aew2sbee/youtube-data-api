# YouTube-視聴者別視聴時間取得スクリプト
実行結果サンプル
```md
🥇今月の勉強時間ランキング(YYYY/MM/DD時点)
1. Aさん: 13時間58分(+1時間40分)
2. Bさん: 3時間38分(+0分)
3. Cさん: 7時間25分(+40分)
```

## 0. 環境構築
0. 環境変数
```bash
touch .env
```
1. `YOUTUBE_API_KEY`と`VIDEO_ID`の記載
```plaintext
YOUTUBE_API_KEY=XXXXXXXXXXXXXXXXX
VIDEO_ID=XXXXXXXXXXXX
```
2. インストール
```bash
pip install -r requirements.txt
```

## 1. スクリプト実行
```bash
python src/main.py
```

## 2. Docker
1. コンテナを起動
```bash
docker-compose up
```
2. コンテナを再起動
```bash
docker-compose restart
```
3. コンテナを停止
```bash
docker-compose down
```