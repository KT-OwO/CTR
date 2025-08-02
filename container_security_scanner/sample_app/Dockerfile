# 古い、潜在的に脆弱なベースイメージを使用
FROM python:3.8-slim-buster

WORKDIR /app

# アプリケーションファイル
COPY requirements.txt requirements.txt
COPY app.py app.py

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリが実行されるポートを公開
EXPOSE 5000

# アプリケーションを実行するコマンド
CMD ["python", "app.py"]
