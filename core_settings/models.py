from django.db import models

from .color_utils import DEFAULT_HEX, normalize_hex


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=255, default="GÖLGEDE YAŞAM")
    logo = models.ImageField(upload_to='site/', null=True, blank=True)
    company_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Firma Telefonu")
    company_address = models.TextField(blank=True, null=True, verbose_name="Firma Adresi")
    sidebar_profile_name = models.CharField(max_length=100, default="Yönetici", verbose_name="Sol Alt Profil Adı")
    sidebar_profile_role = models.CharField(max_length=100, default="Admin", verbose_name="Sol Alt Profil Ünvanı")

    openai_api_key = models.CharField(max_length=255, blank=True, null=True, verbose_name="OpenAI API Key")
    google_api_key = models.CharField(max_length=255, blank=True, null=True, verbose_name="Google AI (Gemini) API Key")
    ai_chat_enabled = models.BooleanField(default=False, verbose_name="Yapay Zeka Sohbet Aktif")
    ai_system_prompt = models.TextField(
        blank=True,
        null=True,
        default="Sen bir asistanasın. Kullanıcının sorularını yanıtla ve ona yardımcı ol.",
        verbose_name="Yapay Zeka Sistem Talimatı",
    )

    class Meta:
        verbose_name = "Site Ayarları"
        verbose_name_plural = "Site Ayarları"

    def __str__(self):
        return self.site_name


class ColorOptionMixin(models.Model):
    color = models.CharField(max_length=7, default='#3b82f6', verbose_name="Renk")

    class Meta:
        abstract = True

    _COLOR_KIND = {
        'ServiceTypeOption': 'service_type',
        'ProductOption': 'product',
        'StatusOption': 'status',
        'PriorityOption': 'priority',
    }

    @property
    def color_hex(self):
        kind = self._COLOR_KIND.get(self.__class__.__name__, 'status')
        return normalize_hex(self.color, fallback=DEFAULT_HEX.get(kind, '#3b82f6'))

    def save(self, *args, **kwargs):
        kind = self._COLOR_KIND.get(self.__class__.__name__, 'status')
        self.color = normalize_hex(self.color, fallback=DEFAULT_HEX.get(kind, '#3b82f6'))
        super().save(*args, **kwargs)


class ServiceTypeOption(ColorOptionMixin, models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Servis tipi"
        verbose_name_plural = "Servis tipleri"

    def __str__(self):
        return self.name


class ProductOption(ColorOptionMixin, models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='box')
    service_types = models.ManyToManyField(
        ServiceTypeOption,
        blank=True,
        related_name='products',
        verbose_name='İzin verilen arıza / servis tipleri',
    )

    class Meta:
        verbose_name = "Ürün seçeneği"
        verbose_name_plural = "Ürün seçenekleri"

    def __str__(self):
        return self.name


class StatusOption(ColorOptionMixin, models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Servis durumu"
        verbose_name_plural = "Servis durumları"

    def __str__(self):
        return self.name


class WhatsAppTemplate(models.Model):
    title = models.CharField(max_length=100, verbose_name="Şablon Başlığı")
    message = models.TextField(verbose_name="Mesaj İçeriği")

    class Meta:
        verbose_name = "WhatsApp Şablonu"
        verbose_name_plural = "WhatsApp Şablonları"

    def __str__(self):
        return self.title


class PriorityOption(ColorOptionMixin, models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Öncelik"
        verbose_name_plural = "Öncelikler"

    def __str__(self):
        return self.name


class SolutionPartnerType(models.Model):
    name = models.CharField(max_length=80, unique=True, verbose_name='Tür adı')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')

    class Meta:
        verbose_name = 'Çözüm ortağı türü'
        verbose_name_plural = 'Çözüm ortağı türleri'
        ordering = ['name']

    def __str__(self):
        return self.name


class ServiceTeam(models.Model):
    name = models.CharField(max_length=80, unique=True, verbose_name='Ekip adı')
    product_groups = models.ManyToManyField(
        ProductOption,
        blank=True,
        related_name='skilled_teams',
        verbose_name='Yetenekli ürün grupları',
    )
    company_phone = models.CharField(max_length=30, blank=True, null=True, verbose_name='Şirket hattı')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')

    class Meta:
        verbose_name = 'Servis ekibi'
        verbose_name_plural = 'Servis ekipleri'
        ordering = ['name']

    def __str__(self):
        return self.name


class ServicePersonnel(models.Model):
    name = models.CharField(max_length=120, verbose_name='Ad Soyad')
    team = models.ForeignKey(
        ServiceTeam,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personnel',
        verbose_name='Ekip',
    )
    product_groups = models.ManyToManyField(
        ProductOption,
        blank=True,
        related_name='skilled_personnel',
        verbose_name='Yetenekli ürün grupları',
    )
    company_phone = models.CharField(max_length=30, blank=True, null=True, verbose_name='Şirket numarası')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    notes = models.CharField(max_length=255, blank=True, null=True, verbose_name='Not')

    class Meta:
        verbose_name = 'Servis personeli'
        verbose_name_plural = 'Servis personelleri'
        ordering = ['name']

    def __str__(self):
        return self.name


class SolutionPartner(models.Model):
    name = models.CharField(max_length=120, verbose_name='Ad')
    partner_type = models.ForeignKey(
        SolutionPartnerType,
        on_delete=models.PROTECT,
        related_name='partners',
        null=True,
        blank=True,
        verbose_name='Tür',
    )
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name='Telefon')
    notes = models.CharField(max_length=255, blank=True, null=True, verbose_name='Not')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')

    class Meta:
        verbose_name = 'Çözüm ortağı'
        verbose_name_plural = 'Çözüm ortakları'
        ordering = ['name']

    def __str__(self):
        type_name = self.partner_type.name if self.partner_type else 'Türsüz'
        return f'{self.name} ({type_name})'


