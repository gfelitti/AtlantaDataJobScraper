#!/bin/bash
set -e

# Ensure DB directory exists
mkdir -p "$(dirname "$DB_PATH")"

# Export env vars for cron (cron doesn't inherit Docker env)
printenv | grep -E '^(DB_PATH|ANTHROPIC_API_KEY|RESEND_API_KEY|EMAIL_FROM|EMAIL_TO|RESEND_AUDIENCE_ID)=' > /etc/environment

# Initial scrape on startup (background, so frontend starts immediately)
python3 /app/main.py --all --db "$DB_PATH" &

# Start cron daemon
cron

# Start Next.js frontend
cd /app/frontend && node_modules/.bin/next start -p "${PORT:-3000}"
