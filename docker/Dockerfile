# ===================================
# A股自选股智能分析系统 - Docker 镜像
# ===================================

FROM node:20-slim AS web-builder

WORKDIR /app/apps/dsa-web

COPY apps/dsa-web/package.json apps/dsa-web/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY apps/dsa-web/ ./
RUN npm run build

FROM python:3.11-slim-bookworm

WORKDIR /app

ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    LOG_DIR=/app/logs \
    DATABASE_PATH=/app/data/stock_analysis.db \
    WEBUI_HOST=0.0.0.0 \
    PORT=8000

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

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY *.py ./
COPY api/ ./api/
COPY data_provider/ ./data_provider/
COPY bot/ ./bot/
COPY patch/ ./patch/
COPY src/ ./src/
COPY strategies/ ./strategies/
COPY --from=web-builder /app/apps/dsa-web/dist ./static/

RUN mkdir -p /app/data /app/logs /app/reports

EXPOSE 8000
VOLUME ["/app/data", "/app/logs", "/app/reports"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD sh -c 'curl -fsS http://localhost:${PORT:-8000}/api/health || curl -fsS http://localhost:${PORT:-8000}/health || exit 1'

CMD ["sh", "-c", "export WEBUI_HOST=0.0.0.0 && export WEBUI_PORT=${PORT:-8000} && export API_PORT=${PORT:-8000} && exec python main.py --webui-only"]
