from django.conf import settings
from django.db import models
from decimal import Decimal


class SalesLead(models.Model):
    STATUS_COMPLETED = 'completed'
    STATUS_PENDING = 'pending'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_COMPLETED, 'Tamamlandı'),
        (STATUS_PENDING, 'Beklemede'),
        (STATUS_CANCELLED, 'İptal'),
    )

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='sales_leads',
        verbose_name='Müşteri',
    )
    sale_date = models.DateField(verbose_name='Tarih')
    project = models.CharField(max_length=255, verbose_name='Proje')
    products = models.ManyToManyField(
        'core_settings.ProductOption',
        blank=True,
        related_name='sales_leads',
        verbose_name='Proje ürünleri',
    )
    sale_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Toplam (₺)',
    )
    down_payment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Peşinat (₺)',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='sales_leads',
        verbose_name='Satış Temsilcisi',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_COMPLETED,
        verbose_name='Durum',
    )
    notes = models.TextField(blank=True, null=True, verbose_name='Not')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sale_date', '-created_at']
        verbose_name = 'Satış Kaydı'
        verbose_name_plural = 'Satış Kayıtları'

    def __str__(self):
        return f'{self.customer.name} — {self.sale_date}'

    @property
    def service_count(self):
        return self.customer.service_records.count()

    @property
    def project_display(self):
        if self.project:
            return self.project
        lines = list(self.product_lines.select_related('product').all())
        if lines:
            return ', '.join(
                f'{line.product.name}×{line.quantity}' for line in lines
            )
        names = [p.name for p in self.products.all()]
        if names:
            return ', '.join(names)
        names = [p.name for p in self.customer.products.all()]
        return ', '.join(names) if names else '—'

    @property
    def interim_payments_total(self):
        return sum(
            (p.amount or Decimal('0')) for p in self.interim_payments.all()
        )

    @property
    def interim_payments_summary(self):
        payments = list(self.interim_payments.all())
        if not payments:
            return ''
        return ' + '.join(f'{p.amount:.2f} ₺' for p in payments)

    @property
    def remaining_balance(self):
        total = self.sale_amount or Decimal('0')
        paid = (self.down_payment or Decimal('0')) + self.interim_payments_total
        return total - paid


class SalesLeadInterimPayment(models.Model):
    sales_lead = models.ForeignKey(
        SalesLead,
        on_delete=models.CASCADE,
        related_name='interim_payments',
        verbose_name='Satış kaydı',
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Tutar (₺)',
    )
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='Sıra')

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Ara ödeme'
        verbose_name_plural = 'Ara ödemeler'

    def __str__(self):
        return f'{self.amount} ₺'


class SalesLeadProductLine(models.Model):
    sales_lead = models.ForeignKey(
        SalesLead,
        on_delete=models.CASCADE,
        related_name='product_lines',
        verbose_name='Satış kaydı',
    )
    product = models.ForeignKey(
        'core_settings.ProductOption',
        on_delete=models.PROTECT,
        related_name='sales_product_lines',
        verbose_name='Ürün',
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='Adet')
    color = models.ForeignKey(
        'core_settings.ProductColorOption',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='sales_product_lines',
        verbose_name='Renk',
    )
    note = models.CharField(max_length=500, blank=True, null=True, verbose_name='Ürün notu')
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='Sıra')

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Proje ürünü'
        verbose_name_plural = 'Proje ürünleri'

    def __str__(self):
        parts = [f'{self.product.name}×{self.quantity}']
        if self.color:
            parts.append(self.color.name)
        return ' — '.join(parts)
