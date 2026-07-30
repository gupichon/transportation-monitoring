FROM python:3.12-slim
LABEL authors="pichong"
WORKDIR /app

COPY stops_monitoring.yaml docker/requirements.txt ./
COPY transportation_monitoring ./transportation_monitoring
RUN pip install --no-cache-dir -r requirements.txt
