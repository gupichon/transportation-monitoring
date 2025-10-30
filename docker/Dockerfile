FROM python:3.12-slim
LABEL authors="pichong"
WORKDIR /app

COPY secrets.yaml stops_monitoring.yaml ./
COPY transportation_monitoring ./transportation_monitoring
COPY docker/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
