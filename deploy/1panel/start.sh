#!/usr/bin/env bash
# 1Panel / Linux production başlatma (Supervisor veya "çalıştırma komutu" olarak kullanın)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

if [ ! -f "venv/bin/activate" ]; then
  echo "venv yok. Önce: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi
# shellcheck source=/dev/null
source venv/bin/activate

export DJANGO_SETTINGS_MODULE=config.settings

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py sync_permissions 2>/dev/null || true

HOST="${DAPHNE_HOST:-127.0.0.1}"
PORT="${DAPHNE_PORT:-8000}"

exec daphne -b "$HOST" -p "$PORT" config.asgi:application
