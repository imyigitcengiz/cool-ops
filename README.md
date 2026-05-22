# GY Panel (CRM / servis dashboard)

Django tabanlı CRM ve servis paneli — müşteri başına ayrı sunucuda kurulur.

## Üretim

**[DEPLOY.md](DEPLOY.md)** — Docker Compose, Coolify, 1Panel, ortam değişkenleri, WhatsApp köprüsü.

```bash
docker compose up -d --build
```

- Kalıcı veri: volume `/data`
- WhatsApp: `whatsapp-bridge` servisi (panel ile birlikte `compose.yaml`)

Coolify notları: [deploy/coolify/README.md](deploy/coolify/README.md)

## Yerel geliştirme

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

WhatsApp (yerel): `tools/whatsapp_bridge` → `npm install && npm start`  
veya `DJANGO_WHATSAPP_BRIDGE_AUTO_START=1` ile runserver otomatik dener.
