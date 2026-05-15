FROM node:22-alpine AS frontend
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src
RUN npm run build

FROM python:3.12-slim AS backend
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend ./backend
COPY scripts ./scripts
COPY --from=frontend /app/dist ./dist

# 회사 시공표준 PDF 사전 파싱 (pdfplumber 고급파싱)
# preload/ 폴더의 PDF가 있으면 rag_index.json + documents/ 자동 생성
RUN python /app/scripts/preload_document.py || echo "preload skipped (PDF not found)"

WORKDIR /app/backend
EXPOSE 8000
# Render injects $PORT; locally defaults to 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
