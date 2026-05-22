#!/usr/bin/env bash
# İlk kurulum (sunucuda bir kez)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
$PYTHON -m venv venv
# shellcheck source=/dev/null
source venv/bin/activate

pip install -U pip
pip install -r requirements.txt

if [ ! -f .env ] && [ -f deploy/1panel/.env.example ]; then
  cp deploy/1panel/.env.example .env
  echo ".env oluşturuldu — deploy/1panel/.env.example içeriğini düzenleyin."
fi

export DJANGO_SETTINGS_MODULE=config.settings
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py sync_permissions --reset-system-roles

echo "Kurulum tamam. Başlatma: bash deploy/1panel/start.sh"
