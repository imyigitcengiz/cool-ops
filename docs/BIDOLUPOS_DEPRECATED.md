# BiDoluPos backend — kullanımdan kaldırıldı

BiDoluPos'un ayrı Django backend'i (`BiDoluPos/backend/`) artık kullanılmamalıdır.

Tüm restoran POS iş mantığı ve API'ler KobiHub `restaurant` uygulamasında birleştirildi:

- API: `/restoran/api/`
- SPA: `/restoran/`
- Kayıt: `/kayit/?vertical=restaurant`
- Yönetim: `/yonetim/`

Yerel `BiDoluPos/` klasörü yalnızca referans olarak tutulabilir; canlı geliştirme `KobiHub` `restoran-pos` dalında yapılır.
