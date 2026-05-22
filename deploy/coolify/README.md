# Coolify kurulumu

Tek üretim yolu: **GitHub + Dockerfile + `/data` volume**.

## 1. Coolify uygulaması

| Ayar | Değer |
|------|--------|
| Kaynak | `https://github.com/imyigitcengiz/gy-dashboard-py` |
| Branch | `main` |
| Build | **Dockerfile** (kök) |
| Port (container) | `8000` |
| Health check | `/giris/` (Dockerfile’da tanımlı) |

## 2. Kalıcı depolama (zorunlu)

**Persistent Storage** ekleyin:

- **Mount path:** `/data`
- İçerik: `db.sqlite3`, `media/`

Volume yoksa her deploy’da veritabanı sıfırlanır.

## 3. Ortam değişkenleri

`deploy/coolify/.env.example` dosyasını Coolify **Environment** alanına kopyalayın.

Minimum:

```env
DJANGO_SECRET_KEY=...
DJANGO_ALLOWED_HOSTS=panel.sizin.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://panel.sizin.com
DJANGO_SECURE_SSL=1
DJANGO_ENSURE_SUPERADMIN=1
```

İlk girişten sonra `DJANGO_ENSURE_SUPERADMIN=0` yapıp redeploy edin.

`DATA_DIR`, `DJANGO_DB_PATH`, `DJANGO_MEDIA_ROOT` Dockerfile’da hazır; Coolify’da tekrar yazmanız gerekmez.

## 4. Domain

- Domain ekleyin, HTTPS açın
- `ALLOWED_HOSTS` ve `CSRF_TRUSTED_ORIGINS` tam domain ile eşleşmeli

## 5. Deploy

Logda beklenen:

```text
[gy-dashboard] migrate + collectstatic...
[gy-dashboard] daphne 0.0.0.0:8000
```

## Veri taşıma (önerilen: SQLite)

1. Lokal: `/tools/yedekler/` → **db.sqlite3 İndir**
2. Sunucu: aynı sayfa → **SQLite İçe Aktar** → dosya `/data/db.sqlite3` olur
3. Lokal `media/` → `docker cp ./media/. <container>:/data/media/`

Alternatif: JSON.gz (aynı sayfada).

## Sorun giderme

| Belirti | Çözüm |
|---------|--------|
| Container kapanıyor | Logs; `PORT` ve entrypoint `0.0.0.0` |
| 400 DisallowedHost | `DJANGO_ALLOWED_HOSTS` |
| CSRF | `DJANGO_CSRF_TRUSTED_ORIGINS` https URL |
| DB sıfırlanıyor | Volume `/data` |
| WhatsApp “başlatılıyor” | Sadece panel konteyneri yetmez; köprü servisi gerekir (aşağı) |

## 6. WhatsApp köprüsü (zorunlu — mesaj / QR için)

Panel imajında Node yoktur. İki yol:

### A) Docker Compose (önerilen)

Coolify’da **Docker Compose** kaynağı: repo kökündeki `compose.yaml` veya `deploy/coolify/compose.yaml`.

- `app` + `whatsapp-bridge` birlikte ayağa kalkar
- App ortamı: `WHATSAPP_BRIDGE_URL=http://whatsapp-bridge:3939`
- Köprü oturumu: volume `whatsapp_session`

### B) İki ayrı Coolify uygulaması

1. **Panel** — kök `Dockerfile`, port 8000, volume `/data`
2. **Köprü** — `deploy/whatsapp-bridge/Dockerfile`, port 3939 (dışarı açmayın)

Aynı Coolify projesinde internal hostname ile panelde:

```env
WHATSAPP_BRIDGE_URL=http://<köprü-container-hostname>:3939
DJANGO_WHATSAPP_BRIDGE_CAN_SPAWN=0
```

Köprü logları: `docker logs` — Chromium/QR hataları burada görünür.

## Yerel Docker test (isteğe bağlı)

```bash
docker build -t gy-dashboard .
docker run --rm -p 8000:8000 -v gy_data:/data \
  -e DJANGO_SECRET_KEY=test -e DJANGO_ALLOWED_HOSTS=localhost \
  -e DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000 \
  -e DJANGO_ENSURE_SUPERADMIN=1 \
  gy-dashboard
```
