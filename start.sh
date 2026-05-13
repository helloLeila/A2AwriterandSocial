#!/bin/sh
set -e

# 启动后端 (后台)
echo "Starting FastAPI backend..."
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-access-log &

# 等待后端启动
sleep 3

# 启动 Nginx (前台，保持容器运行)
echo "Starting Nginx..."
nginx -g 'daemon off;'
