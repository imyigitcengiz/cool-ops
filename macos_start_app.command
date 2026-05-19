#!/usr/bin/env bash
# macOS: Çift tık veya ./macos_start_app.command — yalnızca başlatır; kurulum yapmaz.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/startup-$(date +%Y%m%d-%H%M%S).log"
LATEST_LOG="$LOG_DIR/latest-macos.log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

show_setup_guide() {
  cat <<EOF

╔══════════════════════════════════════════════════════════════╗
║  Kurulum gerekli — aşağıdaki adımları Terminal'de uygulayın  ║
╚══════════════════════════════════════════════════════════════╝

1) Python 3.10–3.13 kurun (3.14 önerilmez):
     brew install python@3.12
   veya https://www.python.org/downloads/

2) Proje klasörüne gidin:
     cd "$ROOT"

3) Sanal ortam oluşturun:
     python3 -m venv venv

4) Sanal ortamı etkinleştirin:
     source venv/bin/activate

5) Bağımlılıkları kurun:
     pip install -r requirements.txt

6) Veritabanını hazırlayın:
     python manage.py migrate

7) Bu dosyayı tekrar çalıştırın:
     ./macos_start_app.command

EOF
}

pause_exit() {
  echo ""
  read -r -p "Kapatmak için Enter'a basın..." _
  exit 1
}

exec > >(tee -a "$LOG_FILE") 2>&1
ln -sf "$(basename "$LOG_FILE")" "$LATEST_LOG" 2>/dev/null || cp -f "$LOG_FILE" "$LATEST_LOG"

log "=== GY Dashboard (macOS) ==="
log "Proje: $ROOT"

if [ ! -f "venv/bin/activate" ]; then
  log "Sanal ortam bulunamadı (venv/bin/activate)."
  show_setup_guide
  log "Log: $LOG_FILE"
  pause_exit
fi

if [ ! -f "venv/bin/python" ]; then
  log "Sanal ortam bozuk veya Windows'tan kopyalanmış olabilir."
  echo ""
  echo "  venv klasörünü silip kurulum adımlarını baştan uygulayın:"
  echo "    rm -rf venv"
  show_setup_guide
  log "Log: $LOG_FILE"
  pause_exit
fi

# shellcheck source=/dev/null
source venv/bin/activate

if ! python -c "import django" 2>/dev/null; then
  log "Django yüklü değil; bağımlılıklar kurulmamış."
  show_setup_guide
  log "Log: $LOG_FILE"
  pause_exit
fi

log "Python: $(python --version 2>&1)"

LAN_IP="$(python -c "
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    print(s.getsockname()[0])
    s.close()
except OSError:
    pass
" 2>/dev/null || true)"

log "Bu bilgisayar:     http://127.0.0.1:8000"
if [ -n "$LAN_IP" ]; then
  log "Aynı WiFi ağı:     http://${LAN_IP}:8000"
  echo ""
  echo "  Diğer cihazlarda (telefon, tablet) tarayıcıya yazın:"
  echo "  http://${LAN_IP}:8000"
  echo ""
else
  log "WiFi IP bulunamadı; Sistem Ayarları > Ağ’dan IP’nizi kontrol edin."
fi
log "Durdurmak: Ctrl+C  |  Log: $LOG_FILE"

python manage.py runserver 0.0.0.0:8000
