# 多阶段构建：前端 + 后端 单容器部署

# === Stage 1: 构建前端 ===
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# === Stage 2: Python 后端基础镜像 ===
FROM python:3.11-slim AS backend

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 复制前端构建产物到 Nginx 目录
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

# Nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 环境变量默认值（生产环境请通过 Sealos 控制台覆盖）
ENV ANTHROPIC_API_KEY=""
ENV APP_ENV=production
ENV CORS_ORIGINS="*"

# 暴露端口
EXPOSE 80

# 启动脚本：同时启动 nginx 和 uvicorn
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
