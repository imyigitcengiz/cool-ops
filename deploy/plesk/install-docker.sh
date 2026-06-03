#!/usr/bin/env bash
# Plesk sunucusunda Docker + Compose v2 (bir kez, root/SSH)
set -euo pipefail

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  echo "Docker ve docker compose zaten kurulu."
  docker --version
  docker compose version
  exit 0
fi

echo "Docker kuruluyor (get.docker.com)..."
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker 2>/dev/null || service docker start 2>/dev/null || true

if ! docker compose version >/dev/null 2>&1; then
  echo "HATA: docker compose plugin bulunamadı. Plesk Docker eklentisini güncelleyin veya Docker CE 24+ kurun."
  exit 1
fi

echo "OK:"
docker --version
docker compose version
echo ""
echo "Plesk Git kullanıcısını docker grubuna ekleyin (örnek):"
echo "  usermod -aG docker <plesk-system-user>"
