FROM python:3.12-slim
LABEL authors="pichong"
WORKDIR /app

COPY ../secrets.yaml ../stops_monitoring.yaml ./

RUN pip install -r requirements.txt
