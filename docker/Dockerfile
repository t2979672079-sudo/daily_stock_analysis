# ===================================
# A股自选股智能分析系统 - Docker 镜像
# ===================================
# 多阶段构建：前端打包 + 后端运行

FROM node:20-slim AS web-builder

WORKDIR /app/apps/dsa-web

COPY apps/dsa-web/package.json apps/dsa-web/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY apps/dsa-web/ ./
RUN npm run build

# 运行阶段
FROM python:3.11-slim-bookworm

# 工作目录
WORKDIR /app

# 基础环境变量
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    LOG_DIR=/app/logs \
    DATABASE_PATH=/app/data/stock_analysis.db \
    WEBUI_HOST=0.0.0.0 \
    PORT=8000

# 设置时区 + 安装系统依赖
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    ca-certificates \
    wkhtmltopdf \
    fontconfig \
    libjpeg62-turbo \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用缓存
COPY requirements.txt ./

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制项目代码
COPY *.py ./
COPY api/ ./api/
COPY data_provider/ ./data_provider/
COPY bot/ ./bot/
COPY patch/ ./patch/
COPY src/ ./src/
COPY strategies/ ./strategies/
COPY --from=web-builder /app/apps/dsa-web/dist ./static/

# 创建数据目录
RUN mkdir -p /app/data /app/logs /app/reports

# 对外声明端口（实际监听以 PORT 环境变量为准）
EXPOSE 8000

# 持久化目录
VOLUME ["/app/data", "/app/logs", "/app/reports"]

# 健康检查：必须真正检查到服务
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD sh -c 'curl -fsS http://localhost:${PORT:-8000}/api/health || curl -fsS http://localhost:${PORT:-8000}/health || exit 1'

# 启动 Web 服务
# 这里显式把 Zeabur 的 PORT 注入给项目
CMD ["sh", "-c", "export WEBUI_HOST=0.0.0.0 && export WEBUI_PORT=${PORT:-8000} && export API_PORT=${PORT:-8000} && exec python main.py --webui-only"]
