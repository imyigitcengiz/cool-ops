from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=255, verbose_name="Müşteri Adı")
    phone = models.CharField(max_length=100, verbose_name="Telefon", blank=True, null=True)
    region = models.CharField(max_length=255, verbose_name="Bölge", blank=True, null=True)
    address = models.TextField(verbose_name="Adres", blank=True, null=True)
    location_link = models.URLField(max_length=500, verbose_name="Konum Linki", blank=True, null=True)
    contract_date = models.DateField(null=True, blank=True, verbose_name="Sözleşme Tarihi")
    products = models.ManyToManyField('core_settings.ProductOption', blank=True, verbose_name="Satın Aldığı Ürünler")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def contract_age(self):
        if not self.contract_date:
            return None
        
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        
        diff = relativedelta(timezone.now().date(), self.contract_date)
        parts = []
        if diff.years > 0:
            parts.append(f"{diff.years} yıl")
        if diff.months > 0:
            parts.append(f"{diff.months} ay")
        
        if not parts:
            if diff.days > 0:
                return f"{diff.days} gün"
            return "Bugün"
            
        return " ".join(parts)

    def __str__(self):
        return self.name

    @property
    def whatsapp_link(self):
        if self.phone:
            clean_phone = ''.join(filter(str.isdigit, self.phone))
            if clean_phone.startswith('0'):
                clean_phone = '9' + clean_phone
            elif not clean_phone.startswith('90') and len(clean_phone) == 10:
                clean_phone = '90' + clean_phone
            return f"https://wa.me/{clean_phone}"
        return None
