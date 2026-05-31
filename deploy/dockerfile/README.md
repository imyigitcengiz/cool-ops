# CoolOPS — Dockerfile ile dağıtım (tek konteyner)

Docker Compose seçeneği yoksa repo kökündeki **`Dockerfile`** ile panel + SQLite çalışır.  
WhatsApp köprüsü **ayrı servis olmadan** devre dışı kalır (Compose gerekir).

## Panel ayarları

| Ayar | Değer |
|------|--------|
| Build type | **Dockerfile** (Nixpacks değil) |
| Dockerfile path | `Dockerfile` (repo kökü) |
| **Persistent Storage** | mount **`/data`** ← zorunlu |
| Port | Panelin verdiği port (Coolify `PORT` env) |

## Environment

[dockerfile.env.example](./dockerfile.env.example) → Environment sekmesine yapıştırın.  
`APP_URL` satırını kendi domain'inizle değiştirin (`/` olmadan).

## İlk giriş

- **admin** / **admin**
- Sonra `DJANGO_ENSURE_SUPERADMIN=0` + redeploy

## Otomatik gelenler (`bootstrap-env.sh`)

- `DJANGO_SECRET_KEY` → `/data/.django_secret_key`
- `DJANGO_ALLOWED_HOSTS` / CSRF → `APP_URL` veya Coolify `SERVICE_URL_APP`

## Sık hatalar

| Belirti | Çözüm |
|---------|--------|
| Container Exited / KRİTİK /data | Persistent Storage **`/data`** bağlı mı? |
| DisallowedHost | `APP_URL=http://tam-domain.sslip.io` + redeploy |
| Her rebuild'de veri sıfır | `/data` volume yok — panelden ekleyin |
| WhatsApp kapalı | Normal — Dockerfile modunda köprü yok |

Compose + WhatsApp için: [deploy/README.md](../README.md)
