"""Restoran modülü — BiDoluPos'tan KobiHub BusinessBrand kapsamına taşındı."""

from django.conf import settings
from django.db import models


class RestaurantTenantProfile(models.Model):
    """BusinessBrand üzerinde restoran abonelik / vitrin meta verisi."""

    PLAN_CHOICES = [
        ('starter', 'Starter'),
        ('growth', 'Growth'),
        ('enterprise', 'Enterprise'),
    ]

    brand = models.OneToOneField(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_tenant',
    )
    public_slug = models.SlugField(max_length=100, unique=True, blank=True)
    plan_tier = models.CharField(max_length=20, choices=PLAN_CHOICES, default='starter')
    plan_expiry = models.DateField(blank=True, null=True)
    trial_started_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Restoran kiracı profili'
        verbose_name_plural = 'Restoran kiracı profilleri'

    def __str__(self):
        return f'{self.brand.name} ({self.get_plan_tier_display()})'

    @property
    def plan(self):
        return self.plan_tier

    @property
    def is_active(self):
        return self.brand.is_active


class RestaurantCategory(models.Model):
    brand = models.ForeignKey(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_categories',
    )
    name = models.CharField(max_length=80)
    icon = models.CharField(max_length=50, default='utensils')
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Menü kategorisi'
        verbose_name_plural = 'Menü kategorileri'
        ordering = ('sort_order', 'name')
        unique_together = (('brand', 'name'),)

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    brand = models.ForeignKey(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_menu_items',
    )
    category = models.ForeignKey(
        RestaurantCategory,
        on_delete=models.CASCADE,
        related_name='items',
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    image = models.ImageField(upload_to='restaurant/menu/', blank=True, null=True)

    class Meta:
        verbose_name = 'Menü ürünü'
        verbose_name_plural = 'Menü ürünleri'
        ordering = ('sort_order', 'name')

    def __str__(self):
        return self.name


class RestaurantMenuItemModifier(models.Model):
    menu_item = models.ForeignKey(
        RestaurantMenuItem,
        related_name='modifiers',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=100)
    price_extra = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_required = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} (+{self.price_extra} TL)'


class RestaurantBranch(models.Model):
    brand = models.ForeignKey(
        'core_settings.BusinessBrand',
        related_name='restaurant_branches',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    panel_slug = models.SlugField(max_length=80, unique=True, blank=True, null=True)
    panel_password = models.CharField(max_length=128, blank=True, null=True)
    panel_enabled = models.BooleanField(default=False)
    panel_password_updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('brand', 'name'),)
        verbose_name = 'Restoran şubesi'
        verbose_name_plural = 'Restoran şubeleri'

    def __str__(self):
        return f'{self.name} ({self.brand.name})'


class RestaurantTable(models.Model):
    STATUS_EMPTY = 'empty'
    STATUS_OCCUPIED = 'occupied'
    STATUS_BILL = 'bill_requested'
    STATUS_CHOICES = (
        (STATUS_EMPTY, 'Boş'),
        (STATUS_OCCUPIED, 'Dolu'),
        (STATUS_BILL, 'Hesap istendi'),
    )

    brand = models.ForeignKey(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_tables',
    )
    branch = models.ForeignKey(
        RestaurantBranch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tables',
    )
    name = models.CharField(max_length=50)
    capacity = models.PositiveSmallIntegerField(default=4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_EMPTY)

    class Meta:
        verbose_name = 'Masa'
        verbose_name_plural = 'Masalar'
        unique_together = (('brand', 'branch', 'name'),)

    def __str__(self):
        return self.name


class RestaurantOrder(models.Model):
    STATUS_PREPARING = 'preparing'
    STATUS_READY = 'ready'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_PREPARING, 'Hazırlanıyor'),
        (STATUS_READY, 'Hazır'),
        (STATUS_COMPLETED, 'Tamamlandı'),
        (STATUS_CANCELLED, 'İptal Edildi'),
    )
    DISCOUNT_NONE = 'none'
    DISCOUNT_PERCENT = 'percent'
    DISCOUNT_FIXED = 'fixed'
    DISCOUNT_CHOICES = (
        (DISCOUNT_NONE, 'İndirim Yok'),
        (DISCOUNT_PERCENT, 'Yüzde (%)'),
        (DISCOUNT_FIXED, 'Sabit (TL)'),
    )

    brand = models.ForeignKey(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_orders',
    )
    branch = models.ForeignKey(
        RestaurantBranch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='orders',
    )
    table = models.ForeignKey(RestaurantTable, related_name='orders', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PREPARING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_CHOICES, default=DISCOUNT_NONE)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_reason = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def discounted_total(self):
        if self.discount_type == self.DISCOUNT_PERCENT:
            return max(0, float(self.total_amount) * (1 - float(self.discount_value) / 100))
        if self.discount_type == self.DISCOUNT_FIXED:
            return max(0, float(self.total_amount) - float(self.discount_value))
        return float(self.total_amount)

    def __str__(self):
        return f'Sipariş #{self.id} - {self.table.name}'


class RestaurantOrderItem(models.Model):
    STATUS_CHOICES = (
        ('preparing', 'Hazırlanıyor'),
        ('ready', 'Hazır'),
        ('served', 'Servis Edildi'),
        ('cancelled', 'İptal Edildi'),
    )
    order = models.ForeignKey(RestaurantOrder, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(RestaurantMenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True, null=True)
    modifier_text = models.CharField(max_length=500, blank=True, null=True)
    modifier_extra = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='preparing')

    def __str__(self):
        return f'{self.quantity}x {self.menu_item.name}'


class RestaurantPayment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Nakit'),
        ('card', 'Kredi Kartı'),
    )
    order = models.ForeignKey(RestaurantOrder, related_name='payments', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)


class RestaurantOrderChannel(models.Model):
    brand = models.ForeignKey(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_order_channels',
    )
    name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    endpoint_url = models.URLField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = (('brand', 'name'),)


class RestaurantCashRegister(models.Model):
    brand = models.ForeignKey(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_cash_registers',
    )
    branch = models.ForeignKey(
        RestaurantBranch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cash_registers',
    )
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    location = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = (('brand', 'name'),)


class RestaurantIngredient(models.Model):
    brand = models.ForeignKey(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_ingredients',
    )
    name = models.CharField(max_length=100)
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, default='pcs')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        unique_together = (('brand', 'name'),)


class RestaurantRecipe(models.Model):
    menu_item = models.OneToOneField(
        RestaurantMenuItem,
        related_name='recipe',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=100, blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)


class RestaurantRecipeIngredient(models.Model):
    recipe = models.ForeignKey(RestaurantRecipe, related_name='ingredients', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(RestaurantIngredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='pcs')


class RestaurantStaffMember(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, default='waiter')
    hire_date = models.DateField(blank=True, null=True)


class RestaurantExpense(models.Model):
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    staff_member = models.ForeignKey(
        RestaurantStaffMember,
        related_name='expenses',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )


class RestaurantCourier(models.Model):
    brand = models.ForeignKey(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_couriers',
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=50, default='available')
    cash_advance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)


class RestaurantCourierLog(models.Model):
    courier = models.ForeignKey(RestaurantCourier, related_name='logs', on_delete=models.CASCADE)
    order = models.ForeignKey(RestaurantOrder, related_name='courier_logs', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='assigned')


class RestaurantProfile(models.Model):
    brand = models.OneToOneField(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_profile',
    )
    name = models.CharField(max_length=150, default='Restoran')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tax_office = models.CharField(max_length=100, blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    working_hours = models.CharField(max_length=100, default='09:00 - 23:00')
    active_plan = models.CharField(max_length=50, default='Growth')
    plan_expiry = models.DateField(blank=True, null=True)
    website_slug = models.CharField(max_length=100, default='restoran')
    website_theme_color = models.CharField(max_length=30, default='#6366f1')
    website_banner_text = models.CharField(max_length=255, default='Hoş Geldiniz!')
    website_enable_table_orders = models.BooleanField(default=True)
    website_enable_delivery = models.BooleanField(default=True)
    website_enable_takeaway = models.BooleanField(default=True)
    website_custom_domain = models.CharField(max_length=255, blank=True, null=True)
    website_about_text = models.TextField(blank=True, null=True)
    website_instagram = models.CharField(max_length=100, blank=True, null=True)
    website_facebook = models.CharField(max_length=100, blank=True, null=True)
    website_template = models.CharField(max_length=50, default='Modern Dark')
    website_enable_reservation = models.BooleanField(default=True)
    ext_qr_menu_enabled = models.BooleanField(default=True)
    ext_official_website_enabled = models.BooleanField(default=True)
    ext_crm_enabled = models.BooleanField(default=True)
    ext_whatsapp_enabled = models.BooleanField(default=False)
    ext_live_courier_enabled = models.BooleanField(default=False)


class RestaurantCashTransaction(models.Model):
    register = models.ForeignKey(
        RestaurantCashRegister,
        related_name='transactions',
        on_delete=models.CASCADE,
    )
    transaction_type = models.CharField(max_length=10, choices=[('in', 'Giriş'), ('out', 'Çıkış')])
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            reg = self.register
            if self.transaction_type == 'in':
                reg.balance += self.amount
            else:
                reg.balance -= self.amount
            reg.save()


class RestaurantStockAudit(models.Model):
    brand = models.ForeignKey(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_stock_audits',
        null=True,
        blank=True,
    )
    date = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True, null=True)
    total_variance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)


class RestaurantStockAuditItem(models.Model):
    audit = models.ForeignKey(RestaurantStockAudit, related_name='items', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(RestaurantIngredient, on_delete=models.CASCADE)
    system_stock = models.DecimalField(max_digits=10, decimal_places=2)
    actual_stock = models.DecimalField(max_digits=10, decimal_places=2)
    variance = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_difference = models.DecimalField(max_digits=12, decimal_places=2)


class RestaurantCustomer(models.Model):
    brand = models.ForeignKey(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_customers',
    )
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    total_orders = models.IntegerField(default=0)
    last_order_date = models.DateField(blank=True, null=True)
    subscription_status = models.CharField(max_length=30, default='active')

    class Meta:
        unique_together = (('brand', 'phone'),)


class RestaurantWhatsAppConfig(models.Model):
    brand = models.OneToOneField(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_whatsapp',
    )
    api_key = models.CharField(max_length=255, blank=True, null=True)
    phone_number_id = models.CharField(max_length=100, blank=True, null=True)
    is_auto_message_enabled = models.BooleanField(default=True)
    message_template = models.TextField(
        default='Merhaba {customer_name}, {order_id} nolu siparişiniz alınmıştır.',
    )
    is_live_chat_enabled = models.BooleanField(default=False)
    ask_admin_before_sending = models.BooleanField(default=True)


class RestaurantFranchisePanelToken(models.Model):
    branch = models.ForeignKey(
        RestaurantBranch,
        related_name='panel_tokens',
        on_delete=models.CASCADE,
    )
    key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)


class RestaurantAuditLog(models.Model):
    ACTION_CHOICES = (
        ('impersonate', 'Hesaba Gir'),
        ('brand_enter', 'Mağazaya Gir'),
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='restaurant_audit_actions',
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurant_audit_targets',
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    metadata = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class RestaurantSubscriptionInvoice(models.Model):
    PAYMENT_PROVIDER_CHOICES = (
        ('mock', 'Mock'),
        ('stripe', 'Stripe'),
        ('iyzico', 'iyzico'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Bekliyor'),
        ('paid', 'Ödendi'),
        ('failed', 'Başarısız'),
        ('cancelled', 'İptal'),
    )

    brand = models.ForeignKey(
        'core_settings.BusinessBrand',
        on_delete=models.CASCADE,
        related_name='restaurant_invoices',
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    plan = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    payment_provider = models.CharField(max_length=20, choices=PAYMENT_PROVIDER_CHOICES, default='mock')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    external_id = models.CharField(max_length=255, blank=True, null=True)
    checkout_url = models.URLField(max_length=500, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)


# BiDoluPos API uyumluluk takma adları
Table = RestaurantTable
Category = RestaurantCategory
MenuItem = RestaurantMenuItem
MenuItemModifier = RestaurantMenuItemModifier
Order = RestaurantOrder
OrderItem = RestaurantOrderItem
Payment = RestaurantPayment
OrderChannel = RestaurantOrderChannel
CashRegister = RestaurantCashRegister
Ingredient = RestaurantIngredient
Recipe = RestaurantRecipe
RecipeIngredient = RestaurantRecipeIngredient
StaffMember = RestaurantStaffMember
Expense = RestaurantExpense
Courier = RestaurantCourier
CourierLog = RestaurantCourierLog
CashTransaction = RestaurantCashTransaction
StockAudit = RestaurantStockAudit
StockAuditItem = RestaurantStockAuditItem
Customer = RestaurantCustomer
WhatsAppConfig = RestaurantWhatsAppConfig
Branch = RestaurantBranch
FranchisePanelToken = RestaurantFranchisePanelToken
AuditLog = RestaurantAuditLog
Invoice = RestaurantSubscriptionInvoice
