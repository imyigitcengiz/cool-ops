"""CSV içe aktarma türleri — model alanlarıyla aynı etiketler."""

from __future__ import annotations

from common.csv_mapping import ImportField

# customers.Customer
CUSTOMER_FIELDS = (
    ImportField('name', 'Müşteri Adı', required=True, aliases=('AD SOYAD', 'MÜŞTERİ', 'MUSTERI', 'AD', 'NAME', 'MÜŞTERI ADI')),
    ImportField('phone', 'Telefon', aliases=('TELEFON', 'TEL', 'PHONE')),
    ImportField('region', 'Bölge', aliases=('YER', 'BÖLGE', 'BOLGE', 'REGION')),
    ImportField('address', 'Adres', aliases=('ADRES', 'ADDRESS')),
    ImportField('location_link', 'Konum Linki', aliases=('KONUM', 'KONUM LINKI', 'LOCATION', 'HARITA', 'GOOGLE MAPS')),
    ImportField('contract_date', 'Sözleşme Tarihi', aliases=('SÖZLEŞME', 'SOZLESME', 'SÖZLEŞME TARİHİ', 'SOZLESME TARIHI', 'CONTRACT_DATE')),
    ImportField(
        'products',
        'Satın Aldığı Ürünler',
        aliases=('ÜRÜN', 'URUN', 'URUNLER', 'ÜRÜNLER', 'PRODUCT', 'PRODUCTS', 'SATIN ALDIGI URUNLER'),
    ),
)

# core_settings.FinanceRecord
FINANCE_FIELDS = (
    ImportField('type', 'Tür', required=True, aliases=('TÜR', 'TUR', 'TYPE', 'GELIR_GIDER', 'RECORD_TYPE')),
    ImportField('category', 'Gider kategorisi', aliases=('KATEGORİ', 'KATEGORI', 'CATEGORY', 'GIDER KATEGORISI')),
    ImportField('title', 'Açıklama', required=True, aliases=('AÇIKLAMA', 'ACIKLAMA', 'BAŞLIK', 'BASLIK', 'TITLE')),
    ImportField('amount', 'Tutar', required=True, aliases=('TUTAR', 'MİKTAR', 'MIKTAR', 'AMOUNT')),
    ImportField('date', 'Tarih', aliases=('TARİH', 'TARIH', 'DATE', 'RECORD_DATE')),
    ImportField('account', 'Hesap', aliases=('HESAP', 'KASA', 'ACCOUNT', 'CASH_ACCOUNT')),
    ImportField('sales_id', 'Satış / proje (ID)', aliases=('SATIŞ_ID', 'SATIS_ID', 'SALES_ID', 'SATIS PROJE ID')),
    ImportField('customer', 'Satış etiketi', aliases=('SATIŞ_ETİKET', 'SATIS_ETIKET', 'MÜŞTERİ ADI', 'MUSTERI', 'CUSTOMER')),
    ImportField('project', 'Operasyon projesi', aliases=('PROJE', 'PROJECT', 'OPERASYON PROJESI')),
    ImportField('notes', 'Not', aliases=('NOT', 'NOTLAR', 'NOTES')),
)

# core_settings.PersonnelPayment
PAYROLL_FIELDS = (
    ImportField('period', 'Maaş dönemi', aliases=('DÖNEM', 'DONEM', 'PERIOD', 'MAAS DONEMI')),
    ImportField('personnel', 'Personel', required=True, aliases=('PERSONEL', 'AD SOYAD', 'AD', 'PERSONEL ADI')),
    ImportField('type', 'Tür', required=True, aliases=('TÜR', 'TUR', 'TYPE', 'ODEME TURU', 'PAYMENT_TYPE')),
    ImportField('amount', 'Tutar', required=True, aliases=('TUTAR', 'MİKTAR', 'MIKTAR', 'AMOUNT')),
    ImportField('date', 'Ödeme tarihi', aliases=('TARİH', 'TARIH', 'ÖDEME TARİHİ', 'ODEME TARIHI', 'PAYMENT_DATE')),
    ImportField('notes', 'Not', aliases=('NOT', 'NOTLAR', 'NOTES')),
)

# Müşteri rehberi CSV’sinde isteğe bağlı satış sütunları (sales.manage gerekir)
CUSTOMER_SALES_EXTRA_FIELDS = (
    ImportField('project', 'Proje', aliases=('PROJE', 'PROJE ADI', 'PROJECT')),
    ImportField('date', 'Tarih', aliases=('TARİH', 'TARIH', 'SATIŞ TARİHİ', 'SATIS TARIHI', 'SALE_DATE')),
    ImportField('total', 'Toplam (₺)', aliases=('TOPLAM', 'TUTAR', 'SATIŞ TUTARI', 'SALE_AMOUNT')),
    ImportField('down_payment', 'Peşinat (₺)', aliases=('PEŞİNAT', 'PESINAT', 'DOWN_PAYMENT')),
    ImportField('notes', 'Satış notu', aliases=('SATIS NOTU', 'SATIŞ NOTU', 'NOT', 'NOTLAR', 'NOTES')),
)

CUSTOMER_SALE_FIELD_KEYS = frozenset(f.key for f in CUSTOMER_SALES_EXTRA_FIELDS)

# sales_leads.SalesLead (+ müşteri alanları)
SALES_FIELDS = (
    ImportField('customer_name', 'Müşteri Adı', required=True, aliases=('AD SOYAD', 'MÜŞTERİ', 'MUSTERI', 'AD', 'MUSTERI ADI')),
    ImportField('phone', 'Telefon', aliases=('TELEFON', 'TEL', 'PHONE')),
    ImportField('region', 'Bölge', aliases=('YER', 'BÖLGE', 'BOLGE', 'REGION')),
    ImportField('project', 'Proje', aliases=('PROJE', 'PROJE ADI', 'PROJECT')),
    ImportField('products', 'Proje ürünleri', aliases=('ÜRÜN', 'URUN', 'URUNLER', 'ÜRÜNLER', 'PRODUCT', 'PRODUCTS', 'PROJE URUNLERI')),
    ImportField('date', 'Tarih', aliases=('TARİH', 'TARIH', 'SATIŞ TARİHİ', 'SATIS TARIHI', 'SALE_DATE')),
    ImportField('total', 'Toplam (₺)', aliases=('TOPLAM', 'TUTAR', 'SATIŞ TUTARI', 'SALE_AMOUNT')),
    ImportField('down_payment', 'Peşinat (₺)', aliases=('PEŞİNAT', 'PESINAT', 'DOWN_PAYMENT')),
    ImportField('notes', 'Not', aliases=('NOT', 'NOTLAR', 'NOTES')),
)

# tools.MapsScrapedFirm (manuel firma)
FIRM_FIELDS = (
    ImportField('name', 'Firma adı', required=True, aliases=('FIRMA ADI', 'FIRMA', 'NAME', 'AD', 'FIRMA ADI')),
    ImportField('address', 'Adres', aliases=('ADRES', 'ADDRESS')),
    ImportField('phone', 'Telefon', aliases=('TELEFON', 'TEL', 'PHONE')),
    ImportField('website', 'Web sitesi', aliases=('WEB SITESI', 'WEB', 'WEBSITE', 'SITE')),
    ImportField('region', 'Bölge', aliases=('YER', 'BÖLGE', 'BOLGE', 'REGION')),
    ImportField('notes', 'Not', aliases=('NOT', 'NOTLAR', 'NOTES')),
)

IMPORT_TYPES: dict[str, dict] = {
    'customers': {
        'label': 'Müşteriler (rehber)',
        'model': 'customers.Customer',
        'icon': 'users',
        'color': 'brand',
        'permission': 'contact.customers',
        'fields': CUSTOMER_FIELDS,
        'import_note': (
            'Müşteri kartı alanları + isteğe bağlı satış sütunları (Proje, Tarih, Toplam, Peşinat). '
            'Satış sütunları eşlenirse aynı satırdan satış kaydı da oluşturulur; ara ödeme ek sütunlardan okunur. '
            'Ürünler | veya ; ile ayrılabilir.'
        ),
        'import_interim_help': True,
        'redirect_name': 'customers',
        'sample_hint': (
            'Müşteri Adı; Telefon; Bölge; Adres; Konum Linki; Sözleşme Tarihi; Satın Aldığı Ürünler; '
            'Proje; Tarih; Toplam (₺); Peşinat (₺); Ara ödeme tarihi; Ara ödeme; Satış notu'
        ),
    },
    'finance': {
        'label': 'Gelir & gider',
        'model': 'core_settings.FinanceRecord',
        'icon': 'receipt',
        'color': 'emerald',
        'permission': 'accounting.finance',
        'fields': FINANCE_FIELDS,
        'redirect_name': 'tools_csv_hub',
        'sample_hint': 'Tür; Gider kategorisi; Açıklama; Tutar; Tarih; Hesap; Satış / proje (ID); Satış etiketi; Operasyon projesi; Not',
    },
    'payroll': {
        'label': 'Maaş & avans',
        'model': 'core_settings.PersonnelPayment',
        'icon': 'wallet',
        'color': 'violet',
        'permission': 'contact.payroll',
        'fields': PAYROLL_FIELDS,
        'redirect_name': 'tools_csv_hub',
        'sample_hint': 'Maaş dönemi; Personel; Tür; Tutar; Ödeme tarihi; Not',
    },
    'sales': {
        'label': 'Satış kayıtları',
        'model': 'sales_leads.SalesLead',
        'icon': 'badge-dollar-sign',
        'color': 'amber',
        'permission': 'sales.manage',
        'fields': SALES_FIELDS,
        'import_note': 'Müşteri yoksa adından oluşturulur. Proje ürünleri içe aktarılır. Ara ödemeler ek sütunlardan okunur.',
        'import_interim_help': True,
        'redirect_name': 'tools_csv_hub',
        'sample_hint': (
            'Müşteri Adı; Telefon; Bölge; Proje; Proje ürünleri; Tarih; Toplam (₺); Peşinat (₺); '
            'Ara ödeme tarihi; Ara ödeme; Not'
        ),
    },
    'firms': {
        'label': 'Firma rehberi',
        'model': 'tools.MapsScrapedFirm',
        'icon': 'building-2',
        'color': 'rose',
        'permission': 'contact.firms',
        'fields': FIRM_FIELDS,
        'redirect_name': 'tools_csv_hub',
        'sample_hint': 'Firma adı; Adres; Telefon; Web sitesi; Bölge; Not',
    },
}


def import_type_config(slug: str) -> dict | None:
    return IMPORT_TYPES.get(slug)


def user_can_import_sales_with_customers(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    return user.has_perm_codename('sales.manage')


def import_type_fields(slug: str, user=None) -> tuple[ImportField, ...]:
    cfg = import_type_config(slug)
    if not cfg:
        return ()
    fields = list(cfg['fields'])
    if slug == 'customers' and user and user_can_import_sales_with_customers(user):
        existing = {f.key for f in fields}
        for field in CUSTOMER_SALES_EXTRA_FIELDS:
            if field.key not in existing:
                fields.append(field)
    return tuple(fields)


def list_import_types_for_user(user) -> list[dict]:
    out = []
    for slug, cfg in IMPORT_TYPES.items():
        perm = cfg.get('permission')
        if user.is_superuser or (perm and user.has_perm_codename(perm)):
            item = {'slug': slug, **{k: v for k, v in cfg.items() if k != 'fields'}}
            if slug == 'customers':
                item['includes_sales_import'] = user_can_import_sales_with_customers(user)
            out.append(item)
    return out


def user_can_import_type(user, slug: str) -> bool:
    cfg = import_type_config(slug)
    if not cfg or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    perm = cfg.get('permission')
    return bool(perm and user.has_perm_codename(perm))
