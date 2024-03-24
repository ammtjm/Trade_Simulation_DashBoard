# ベースイメージとしてPython3.9を使用
FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# アプリケーションの依存関係をインストール
COPY application/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピー
COPY application/ .

# ポートを公開
EXPOSE 8050

# アプリケーションを実行
CMD ["python", "app.py"]