# 1Panel’e kurulum (GY Dashboard)

Windows’taki `windows_start_app.bat` **sunucuda kullanılmaz**. 1Panel’de reverse proxy + **Daphne** (WebSocket/canlı güncelleme için) çalıştırılır.

## Özet

| Ortam | Başlatma |
|--------|----------|
| Windows geliştirme | `windows_start_app.bat` → `runserver` |
| 1Panel / Linux prod | `deploy/1panel/start.sh` → **daphne** |

## 1) Dosyaları sunucuya atın

Projeyi örneğin `/opt/gy-dashboard` altına koyun (git clone veya zip).

Kalıcı olması gerekenler (yedekleyin):

- `db.sqlite3` (veritabanı)
- `media/` (yüklenen dosyalar)
- `.env` (gizli ayarlar)

## 2) İlk kurulum (SSH)

```bash
cd /opt/gy-dashboard
chmod +x deploy/1panel/*.sh
bash deploy/1panel/install.sh
nano .env   # domain ve SECRET_KEY düzenleyin
```

`.env` örneği: `deploy/1panel/.env.example`

## 3) 1Panel’de site + reverse proxy

### A) Önerilen: OpenResty/Nginx site + arka planda Daphne

1. **Web sitesi** oluşturun (domain + SSL).
2. **Reverse proxy** hedefi: `http://127.0.0.1:8000` (veya seçtiğiniz port).
3. Proxy ayarlarında WebSocket desteğini açın (1Panel genelde otomatik ekler):

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

4. **Medya dosyaları** (yüklemeler) için ek location (opsiyonel, performans):

```nginx
location /media/ {
    alias /opt/gy-dashboard/media/;
}
```

Statik dosyalar (`/static/`) uygulama **WhiteNoise** ile servis edilir (`collectstatic` sonrası).

### B) Supervisor (1Panel “Process” / “Supervisor”)

- Komut: `/opt/gy-dashboard/deploy/1panel/start.sh`
- Dizin: `/opt/gy-dashboard`
- Kullanıcı: `www` veya site kullanıcısı
- Otomatik başlat: açık

Elle test:

```bash
cd /opt/gy-dashboard
bash deploy/1panel/start.sh
```

Durdurmak: supervisor restart/stop.

### C) 1Panel “Python” runtime (varsa)

- Startup file: `config.asgi:application`
- Server: **Daphne** (Channels/WebSocket için Gunicorn tek başına yetmez)
- Port: `8000` (sadece localhost; dışarı nginx açar)

## 4) Ortam değişkenleri (.env)

Zorunlu production örneği:

```env
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=...
DJANGO_ALLOWED_HOSTS=panel.sizin-domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://panel.sizin-domain.com
DJANGO_SECURE_SSL=1
```

`python manage.py check --deploy` ile kontrol edin.

## 5) WhatsApp köprüsü (opsiyonel)

Node.js ayrı süreç (port 3939). Django `.env` içinde:

```env
WHATSAPP_BRIDGE_URL=http://127.0.0.1:3939
DJANGO_WHATSAPP_BRIDGE_AUTO_START=0
```

Köprüyü sunucuda ayrı supervisor ile `tools/whatsapp_bridge` altında `npm start` ile çalıştırın. Windows’taki otomatik UAC başlatma Linux’ta yoktur.

## 6) Güncelleme

```bash
cd /opt/gy-dashboard
git pull   # veya yeni dosyaları kopyalayın
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py sync_permissions
# Supervisor / 1Panel process restart
```

## Sorun giderme

- **502**: Daphne çalışıyor mu? `curl -I http://127.0.0.1:8000/`
- **CSRF hatası**: `DJANGO_CSRF_TRUSTED_ORIGINS` https domain ile eşleşmeli
- **Static boş**: `python manage.py collectstatic --noinput`
- **İzin / RBAC**: `python manage.py sync_permissions --reset-system-roles`
