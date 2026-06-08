# BiDoluPos → CoolOPS restoran migrasyonu

> **Dal:** `restoran-pos` · **Stabil taban:** tag `v1-kobi-stable` (`main`)

Canlı deploy `main` dalından devam eder; restoran işi `restoran-pos` dalında tamamlandı.

## Entegrasyon durumu

| Bileşen | Durum |
|---------|-------|
| Tek Django backend (`restaurant` app + `/restoran/api/`) | ✅ |
| React SPA (`frontend/restaurant-pos` → `/restoran/`) | ✅ |
| Birleşik landing (`?vertical=restaurant`) | ✅ |
| Kayıt (`/kayit/?vertical=restaurant`) + 14 gün trial | ✅ |
| Platform yönetim (`/yonetim/`) | ✅ |
| BiDoluPos `backend/` | ⛔ kullanılmıyor |

## API

- Taban: `/restoran/api/`
- Oturum köprüsü: `GET /restoran/api/auth/session-bridge/` (Django session → DRF token)
- Franchise: `/restoran/franchise`
- Public site: `/w/<slug>/`

## Kurulum

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_restaurant_plans
npm run build:restaurant-pos   # isteğe bağlı — SPA derlemesi
python manage.py runserver
```

## BiDoluPos silme checklist

- [x] Backend KobiHub'a taşındı
- [x] React SPA KobiHub altında
- [x] Landing + kayıt birleştirildi
- [ ] Uçtan uca POS testi (staging)
- [ ] `restoran-pos` → `main` merge + deploy
- [ ] Yerel `BiDoluPos/` klasörü silindi
- [ ] `bidolu-pos` GitHub repo archive

## Geri dönüş

```bash
git checkout main
```
