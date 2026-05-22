# GY Dashboard

Django CRM / servis paneli.

## Coolify (üretim)

Kurulum: **[deploy/coolify/README.md](deploy/coolify/README.md)**

- Dockerfile (kök)
- Kalıcı volume: `/data`
- Ortam örneği: `deploy/coolify/.env.example`

## Yerel geliştirme

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

WhatsApp köprüsü (isteğe bağlı): `tools/whatsapp_bridge` → `npm install && npm start`
