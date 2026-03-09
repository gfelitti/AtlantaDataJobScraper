# ── Stage 1: Build Next.js ───────────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.13-slim

# Node.js 20 + cron
RUN apt-get update && \
    apt-get install -y curl gnupg cron && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright Chromium + system deps
RUN playwright install chromium && playwright install-deps chromium

# Scraper
COPY scraper/ scraper/
COPY main.py .
COPY match_cv.py .

# Frontend (built artifacts + node_modules from builder)
COPY --from=frontend-builder /build ./frontend

# Cron: run scraper daily at 7 AM UTC (env vars passed via /etc/environment)
RUN echo '0 7 * * * . /etc/environment; cd /app && python3 main.py --all --db "$DB_PATH" >> /var/log/scraper.log 2>&1' | crontab -

COPY start.sh .
RUN chmod +x start.sh

ENV DB_PATH=/data/jobs.db
ENV PORT=3000
ENV NODE_ENV=production

EXPOSE 3000

CMD ["./start.sh"]
