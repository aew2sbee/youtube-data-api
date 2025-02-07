# Python 3.12.8 の公式イメージを使用
FROM python:3.12.8

# 環境変数の設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# 作業ディレクトリの作成
WORKDIR /app

# 必要なら requirements.txt をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# `python src/main.py` を実行
CMD ["python", "src/main.py"]
