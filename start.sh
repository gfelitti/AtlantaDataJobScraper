#!/bin/bash
set -e

# Ensure DB directory exists
mkdir -p "$(dirname "$DB_PATH")"

# Initial scrape on startup (background, so frontend starts immediately)
python3 /app/main.py --all --db "$DB_PATH" &

# Start cron daemon
cron

# Start Next.js frontend
cd /app/frontend && node_modules/.bin/next start -p "${PORT:-3000}"
