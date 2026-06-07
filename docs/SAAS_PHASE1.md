# SaaS Faz 1 — Düzeltme ve Sertleştirme Planı

> **Kapı kuralı:** Bu dokümandaki P0 maddeleri %100 tamamlanmadan SaaS geliştirme (Faz 2) başlamaz.

## Mevcut mimari özeti

| Katman | URL | Kim |
|--------|-----|-----|
| Platform | `/yonetim/` | Süper admin |
| Marka HQ | `/panel/`, `/panel/abonelik/`, `/panel/ekip/` | Marka yöneticisi |
| Bayi | Tenant URL | Bayi kullanıcıları |
| Modüller | `/contact/`, `/muhasebe/`, … | Marka ekibi (RBAC) |
| Abonelik modülleri | `/panel/abonelik/#moduller` | Abonelik sahibi (plan tavanı içinde) |

---

## A. Güvenlik & kiracı izolasyonu (P0)

### A1. Süper admin erişim modeli
- [x] Süper admin kiracı modüllerine serbest erişim (`/panel/`, `/contact/`, `/muhasebe/`, …)
- [x] Platform yönetimi tek yüz: `/yonetim/` (plan, fatura, roller, site ayarları, denetim)
- [x] `permission_required` / `PermissionRequiredMixin` → `get_real_user()` + kiracı blok (marka ekibi için)
- [x] Test: süper admin `/contact/`, `/panel/` → 200 (engel yok)

### A2. Kiracı veri sızıntısı (IDOR)
- [ ] Tüm CRUD view’larda `filter_by_brand` audit (devam ediyor)
- [x] Müşteri: düzenle/sil/API/özet — marka kapsamı
- [x] Test: `test_tenant_isolation` müşteri cross-brand 404
- [ ] Servis, satış, medya, CSV audit

### A3. Kimlik doğrulama & oturum
- [ ] Üretimde `admin/admin` yok
- [ ] `SECRET_KEY`, `DEBUG=0`, `ALLOWED_HOSTS` checklist
- [ ] `/kayit/` rate limit + e-posta doğrulama veya admin onayı
- [ ] Impersonate audit log
- [ ] Oturum süresi dokümantasyonu

### A4. Yetki yükseltme
- [ ] Marka sahibi sistem `admin` rolünü atayamaz / kısıtlı
- [ ] Özel rolde süper admin izinleri yok (`tools.backup` vb.)
- [ ] Bayi kullanıcısı `/panel/ekip/` erişemez (test)

### A5. Yedekleme güvenliği
- [ ] Fabrika sıfırlama regresyon testleri
- [x] Yedek indirme / fabrika sıfırlama platform denetim günlüğü (`PlatformAuditLog`)
- [ ] Upload boyut + tip doğrulama
- [ ] Yedek dosyaları web root dışında

---

## B. Mimari tutarlılık (P0)

### B1. Rol & yönetim
- [x] `/yonetim/roller/*` canlı (sistem rolleri); marka özel roller `/panel/ekip/roller/`
- [x] Marka paneli ekip yönetimi: `/panel/ekip/`
- [x] Terim standardı (Marka yöneticisi / Bayi / Platform yöneticisi)

### B2. Plan limitleri
- [x] `max_hq_brands`, `max_dealer_panels` (bayi alt panel), `max_users_per_brand`, `max_customers_per_brand`
- [x] Plan modül tavanı (`included_module_slugs`); abonelik sahibi alt küme seçimi `/panel/abonelik/#moduller`
- [x] Süper admin marka sahibi olamaz; modül yönetimi plan formunda
- [ ] Limit UX regresyon testleri (devam)

### B3. Bayi / tenant
- [ ] Bayi-only `/panel/` engeli (regresyon)
- [ ] Tenant path/subdomain testleri

### B4. Süper admin UX
- [x] Giriş → `/yonetim/` veya `next` hedefi
- [x] Marka inceleme → doğrudan marka seçici (impersonate UI kaldırıldı)
- [x] Yedek → `/yonetim/yedekler/`
- [x] Plan / fatura / site ayarları / denetim → `/yonetim/` altında

---

## C. Test kapısı (P0)

- [ ] `test_security`, `test_brand_team`, `test_platform_access`, `test_tenant`
- [ ] Cross-tenant IDOR suite
- [x] Süper admin serbest kiracı erişimi (`test_platform_access`)
- [x] Yönetim entegrasyonu: plan, fatura, roller, marka yaşam döngüsü (`test_admin_provisioning`)
- [ ] Plan limit testleri

### C1. Yönetim paneli entegrasyonu
- [x] Plan CRUD (`/yonetim/planlar/`)
- [x] Fatura listesi + manuel oluşturma (`/yonetim/faturalar/`)
- [x] Sistem rolleri URL'leri 200 (`/yonetim/roller/`)
- [x] Marka sahibi atama, aktifleştir / pasifleştir
- [x] Site ayarları (`/yonetim/ayarlar/`)
- [x] Platform denetim günlüğü (`/yonetim/denetim/`)
- [x] Rapor CSV dışa aktarma

---

## D. Operasyon (P1)

- [ ] DB + media yedek prosedürü
- [ ] `.env.example` güncel
- [ ] Healthcheck + hata izleme planı

---

## Faz 1 tamamlandı kriteri

1. A1–A5 P0 maddeleri ✅
2. IDOR test suite geçiyor ✅
3. Süper admin impersonate dışında tenant verisi yok ✅
4. Plan limitleri üç eksende zorunlu ✅
5. CI yeşil ✅
6. Üretim güvenlik checklist ✅

---

## Faz 2 — SaaS geliştirme (Faz 1 sonrası)

1. E-posta davet akışı
2. Ödeme + plan otomasyonu
3. Bayi sorumlusu rolü
4. Limit UX + upgrade
5. Süper admin tenant metrikleri
6. White-label / özel domain
7. Trial + feature flags
