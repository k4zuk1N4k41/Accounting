# Tomcatベースイメージを使用
FROM python:3.12.4

WORKDIR /usr/src/app
# ソースをここにコピー
COPY . /usr/src/app

#Flaskに環境変数設定
ENV FLASK_APP=accounting.py
ENV FLASK_RUN_HOST=0.0.0.0

# requirements.txtで指定された必要なパッケージをインストール
RUN pip install -r requirements.txt

#sqliteのインストール
RUN apt update && apt install -y sqlite3


