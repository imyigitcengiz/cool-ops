from django import forms
from django.contrib.auth import get_user_model

from .models import Permission, Role

User = get_user_model()

INPUT = 'w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-brand-500 outline-none'
CHECKBOX = 'w-4 h-4 accent-brand-600'


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'slug', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: Depo Sorumlusu'}),
            'slug': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'ornek-rol'}),
            'description': forms.Textarea(attrs={'class': INPUT, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.permission_ids = kwargs.pop('permission_ids', None)
        super().__init__(*args, **kwargs)
        locked = (
            self.instance.pk
            and (
                self.instance.scope in (Role.SCOPE_PLATFORM_SYSTEM, Role.SCOPE_APP_PRESET)
                or self.instance.is_system
            )
        )
        if locked:
            self.fields['slug'].widget.attrs['readonly'] = True

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if self.instance.pk and (
            self.instance.scope in (Role.SCOPE_PLATFORM_SYSTEM, Role.SCOPE_APP_PRESET)
            or self.instance.is_system
        ):
            return self.instance.slug
        return slug

    def save(self, commit=True):
        role = super().save(commit=commit)
        if self.permission_ids is not None:
            perms = Permission.objects.filter(pk__in=self.permission_ids)
            role.permissions.set(perms)
        return role


class AdminRoleForm(RoleForm):
    class Meta(RoleForm.Meta):
        fields = ['name', 'slug', 'description', 'scope', 'app_id']
        widgets = {
            **RoleForm.Meta.widgets,
            'scope': forms.Select(attrs={'class': INPUT}),
            'app_id': forms.Select(attrs={'class': INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scope'].choices = [
            (Role.SCOPE_PLATFORM_SYSTEM, 'Platform sistemi'),
            (Role.SCOPE_APP_PRESET, 'Uygulama şablonu'),
        ]
        if self.instance.pk and self.instance.scope == Role.SCOPE_TENANT_CUSTOM:
            self.fields['scope'].disabled = True
            self.fields['app_id'].disabled = True

    def clean(self):
        cleaned = super().clean()
        scope = cleaned.get('scope')
        if scope == Role.SCOPE_APP_PRESET and not cleaned.get('app_id'):
            self.add_error('app_id', 'Uygulama şablonu için uygulama seçin.')
        if scope == Role.SCOPE_PLATFORM_SYSTEM:
            cleaned['app_id'] = ''
        return cleaned


class AdminUserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Şifre',
        widget=forms.PasswordInput(attrs={'class': INPUT}),
    )
    password2 = forms.CharField(
        label='Şifre (tekrar)',
        widget=forms.PasswordInput(attrs={'class': INPUT}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': INPUT}),
            'first_name': forms.TextInput(attrs={'class': INPUT}),
            'last_name': forms.TextInput(attrs={'class': INPUT}),
            'email': forms.EmailInput(attrs={'class': INPUT}),
            'role': forms.Select(attrs={'class': INPUT}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'role' in self.fields:
            self.fields['role'].queryset = Role.objects.order_by('name')
        self.fields['is_active'].initial = True
        self.fields['username'].help_text = 'Giriş için kullanılır; ekranda ad soyad görünür.'
        self.fields['first_name'].label = 'Ad'
        self.fields['last_name'].label = 'Soyad'

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 != p2:
            raise forms.ValidationError('Şifreler eşleşmiyor.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class AdminSubscriptionOwnerCreateForm(AdminUserCreateForm):
    """Süper admin — abonelik sahibi + ilk marka."""

    brand_name = forms.CharField(
        label='Marka / mağaza adı',
        max_length=255,
        widget=forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn. Cool Servis'}),
    )
    plan = forms.ModelChoiceField(
        label='Abonelik planı',
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': INPUT}),
    )

    class Meta(AdminUserCreateForm.Meta):
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core_settings.models import Plan

        self.fields['plan'].queryset = Plan.objects.filter(is_active=True).order_by('price')
        free = Plan.objects.filter(is_active=True, price=0).order_by('price').first()
        if free:
            self.fields['plan'].initial = free.pk

    def save(self, commit=True):
        from .models import Role

        user = super().save(commit=False)
        admin_role = Role.objects.filter(slug='admin').first()
        if admin_role:
            user.role = admin_role
        plan = self.cleaned_data.get('plan')
        if plan:
            user.plan = plan
        if commit:
            user.save()
        return user


class AdminPlatformUserCreateForm(AdminUserCreateForm):
    """Süper admin — abonelik sahibi, marka kullanıcısı veya platform yöneticisi."""

    ACCOUNT_OWNER = 'owner'
    ACCOUNT_MEMBER = 'member'
    ACCOUNT_SUPERUSER = 'superuser'

    account_type = forms.ChoiceField(
        label='Hesap türü',
        choices=(
            (ACCOUNT_OWNER, 'Abonelik sahibi (yeni marka ile)'),
            (ACCOUNT_MEMBER, 'Marka kullanıcısı (mevcut markaya)'),
            (ACCOUNT_SUPERUSER, 'Platform yöneticisi (süper admin)'),
        ),
        widget=forms.RadioSelect,
    )
    brand_name = forms.CharField(
        label='Marka / mağaza adı',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn. Cool Servis'}),
    )
    plan = forms.ModelChoiceField(
        label='Abonelik planı',
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': INPUT}),
    )
    brand = forms.ModelChoiceField(
        label='Marka',
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': INPUT}),
    )
    membership_role = forms.ChoiceField(
        label='Marka üyeliği',
        choices=(),
        required=False,
        widget=forms.Select(attrs={'class': INPUT}),
    )

    class Meta(AdminUserCreateForm.Meta):
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core_settings.models import BusinessBrand, BrandMembership, Plan

        self.fields['plan'].queryset = Plan.objects.filter(is_active=True).order_by('price')
        free = Plan.objects.filter(is_active=True, price=0).order_by('price').first()
        if free:
            self.fields['plan'].initial = free.pk
        self.fields['brand'].queryset = BusinessBrand.objects.filter(is_active=True).order_by('name')
        self.fields['membership_role'].choices = (
            (BrandMembership.ROLE_MEMBER, 'Ekip üyesi'),
            (BrandMembership.ROLE_DEALER, 'Bayi kullanıcısı'),
            (BrandMembership.ROLE_OWNER, 'Marka sahibi'),
        )
        self.fields['membership_role'].initial = BrandMembership.ROLE_MEMBER
        self.fields['account_type'].initial = self.ACCOUNT_OWNER
        if 'role' in self.fields:
            self.fields['role'].queryset = Role.objects.order_by('name')

    def clean(self):
        cleaned = super().clean()
        account_type = cleaned.get('account_type')
        if account_type == self.ACCOUNT_OWNER:
            if not cleaned.get('brand_name'):
                self.add_error('brand_name', 'Abonelik sahibi için marka adı zorunlu.')
        elif account_type == self.ACCOUNT_MEMBER:
            if not cleaned.get('brand'):
                self.add_error('brand', 'Marka seçin.')
            if not cleaned.get('role'):
                self.add_error('role', 'Rol seçin.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        account_type = self.cleaned_data.get('account_type')
        if account_type == self.ACCOUNT_OWNER:
            admin_role = Role.objects.filter(slug='admin').first()
            if admin_role:
                user.role = admin_role
            plan = self.cleaned_data.get('plan')
            if plan:
                user.plan = plan
        elif account_type == self.ACCOUNT_SUPERUSER:
            user.is_superuser = True
            user.is_staff = True
        if commit:
            user.save()
            if user.is_superuser:
                from users.admin_services import strip_superuser_brand_memberships
                strip_superuser_brand_memberships(user)
        return user


class AdminBrandCreateForm(forms.Form):
    owner = forms.ModelChoiceField(
        label='Abonelik sahibi',
        queryset=None,
        widget=forms.Select(attrs={'class': INPUT}),
    )
    name = forms.CharField(
        label='Marka / mağaza adı',
        max_length=255,
        widget=forms.TextInput(attrs={'class': INPUT}),
    )
    panel_kind = forms.ChoiceField(
        label='Panel türü',
        choices=(),
        widget=forms.Select(attrs={'class': INPUT}),
    )
    parent_brand = forms.ModelChoiceField(
        label='Bağlı merkez marka (bayi için)',
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': INPUT}),
    )
    tenant_routing = forms.ChoiceField(
        label='Erişim yapısı',
        choices=(),
        widget=forms.Select(attrs={'class': INPUT}),
    )
    host_slug = forms.SlugField(
        label='Kalıcı URL kodu',
        max_length=80,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': 'örn. golgede-yasam',
        }),
        help_text='Boş bırakılırsa marka slug kullanılır.',
    )
    legal_name = forms.CharField(
        label='Ticari ünvan',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT}),
    )
    phone = forms.CharField(
        label='Telefon',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT}),
    )

    def __init__(self, *args, **kwargs):
        from common.brand_team import subscription_owners_queryset
        from core_settings.models import BusinessBrand

        super().__init__(*args, **kwargs)
        self.fields['owner'].queryset = subscription_owners_queryset().order_by('username')
        self.fields['panel_kind'].choices = BusinessBrand.PANEL_KIND_CHOICES
        self.fields['tenant_routing'].choices = BusinessBrand.TENANT_ROUTING_CHOICES
        self.fields['parent_brand'].queryset = BusinessBrand.objects.filter(
            is_active=True,
            panel_kind=BusinessBrand.PANEL_HQ,
        ).order_by('name')
        self.fields['panel_kind'].initial = BusinessBrand.PANEL_HQ
        self.fields['tenant_routing'].initial = BusinessBrand.TENANT_SUBDOMAIN

    def clean(self):
        from common.tenant import validate_brand_tenant_key
        from core_settings.models import BusinessBrand

        cleaned = super().clean()
        panel_kind = cleaned.get('panel_kind')
        parent = cleaned.get('parent_brand')
        if panel_kind == BusinessBrand.PANEL_DEALER and not parent:
            self.add_error('parent_brand', 'Bayi paneli için merkez marka seçin.')
        host_slug = cleaned.get('host_slug', '')
        if host_slug is not None:
            try:
                cleaned['host_slug'] = validate_brand_tenant_key(
                    host_slug,
                    panel_kind=panel_kind,
                    parent_brand=parent,
                )
            except ValueError as exc:
                self.add_error('host_slug', str(exc))
        return cleaned


class AdminUserUpdateForm(forms.ModelForm):
    new_password = forms.CharField(
        required=False,
        label='Yeni şifre (opsiyonel)',
        widget=forms.PasswordInput(attrs={'class': INPUT}),
    )
    brands = forms.ModelMultipleChoiceField(
        label='Marka üyelikleri',
        queryset=None,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': INPUT, 'size': 6}),
    )
    default_brand = forms.ModelChoiceField(
        label='Varsayılan marka',
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': INPUT}),
    )

    is_superuser = forms.BooleanField(
        label='Platform yöneticisi (süper admin)',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': CHECKBOX}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'plan', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': INPUT}),
            'first_name': forms.TextInput(attrs={'class': INPUT}),
            'last_name': forms.TextInput(attrs={'class': INPUT}),
            'email': forms.EmailInput(attrs={'class': INPUT}),
            'role': forms.Select(attrs={'class': INPUT}),
            'plan': forms.Select(attrs={'class': INPUT}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX}),
        }

    def __init__(self, *args, **kwargs):
        self.editor = kwargs.pop('editor', None)
        super().__init__(*args, **kwargs)
        from core_settings.models import BusinessBrand, Plan

        brand_qs = BusinessBrand.objects.order_by('name')
        self.fields['brands'].queryset = brand_qs
        self.fields['default_brand'].queryset = brand_qs
        self.fields['role'].queryset = Role.objects.order_by('name')
        self.fields['plan'].queryset = Plan.objects.filter(is_active=True).order_by('price')
        self.fields['username'].help_text = 'Giriş için kullanılır; ekranda ad soyad görünür.'
        self.fields['first_name'].label = 'Ad'
        self.fields['last_name'].label = 'Soyad'
        if self.instance and self.instance.pk:
            memberships = self.instance.brand_memberships.all()
            self.fields['brands'].initial = list(memberships.values_list('brand_id', flat=True))
            default = memberships.filter(is_default=True).first()
            if default:
                self.fields['default_brand'].initial = default.brand_id
            if self.editor and self.editor.is_superuser:
                self.fields['is_superuser'].initial = self.instance.is_superuser
        if self.instance and self.instance.is_superuser:
            self.fields['role'].disabled = True
            self.fields['plan'].disabled = True
            self.fields['brands'].disabled = True
            self.fields['default_brand'].disabled = True
        elif self.instance and self.instance.pk and not (self.editor and self.editor.is_superuser):
            if 'is_superuser' in self.fields:
                del self.fields['is_superuser']

    def clean(self):
        from users.admin_services import can_change_superuser_status

        cleaned = super().clean()
        if self.editor and self.editor.is_superuser and 'is_superuser' in cleaned:
            promote = cleaned['is_superuser']
            ok, reason = can_change_superuser_status(
                self.editor, self.instance, promote=promote,
            )
            if not ok and self.instance.is_superuser != promote:
                raise forms.ValidationError(reason)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('new_password')
        if password:
            user.set_password(password)
        if self.editor and self.editor.is_superuser and 'is_superuser' in self.cleaned_data:
            user.is_superuser = self.cleaned_data['is_superuser']
            if user.is_superuser:
                user.is_staff = True
        if commit:
            user.save()
            if user.is_superuser:
                from users.admin_services import strip_superuser_brand_memberships
                strip_superuser_brand_memberships(user)
        return user


class AdminBrandUpdateForm(forms.ModelForm):
    owner = forms.ModelChoiceField(
        label='Abonelik sahibi',
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': INPUT}),
    )

    class Meta:
        from core_settings.models import BusinessBrand

        model = BusinessBrand
        fields = [
            'name',
            'legal_name',
            'phone',
            'host_slug',
            'panel_kind',
            'parent_brand',
            'tenant_routing',
            'is_active',
            'is_test_store',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT}),
            'legal_name': forms.TextInput(attrs={'class': INPUT}),
            'phone': forms.TextInput(attrs={'class': INPUT}),
            'host_slug': forms.TextInput(attrs={
                'class': INPUT,
                'placeholder': 'örn. golgede-yasam',
            }),
            'panel_kind': forms.Select(attrs={'class': INPUT}),
            'parent_brand': forms.Select(attrs={'class': INPUT}),
            'tenant_routing': forms.Select(attrs={'class': INPUT}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX}),
            'is_test_store': forms.CheckboxInput(attrs={'class': CHECKBOX}),
        }

    def __init__(self, *args, **kwargs):
        from common.brand_team import subscription_owners_queryset
        from core_settings.models import BrandMembership, BusinessBrand

        super().__init__(*args, **kwargs)
        self.fields['is_test_store'].help_text = (
            'İşaretlenirse platform personeli bu markayı test olarak inceleyebilir.'
        )
        self.fields['owner'].queryset = subscription_owners_queryset().order_by('username')
        if self.instance and self.instance.pk:
            owner_mem = BrandMembership.objects.filter(
                brand=self.instance,
                role=BrandMembership.ROLE_OWNER,
            ).select_related('user').first()
            if owner_mem:
                self.fields['owner'].initial = owner_mem.user_id
        self.fields['parent_brand'].queryset = BusinessBrand.objects.filter(
            is_active=True,
            panel_kind=BusinessBrand.PANEL_HQ,
        ).exclude(pk=self.instance.pk if self.instance.pk else None).order_by('name')
        self.fields['parent_brand'].required = False
        self.fields['host_slug'].label = 'Kalıcı URL kodu'
        self.fields['host_slug'].help_text = (
            'Mağazanın kalıcı adres kodu. Boş bırakılırsa slug kullanılır.'
        )

    def clean(self):
        from common.tenant import validate_brand_tenant_key
        from core_settings.models import BusinessBrand

        cleaned = super().clean()
        panel_kind = cleaned.get('panel_kind')
        parent = cleaned.get('parent_brand')
        owner = cleaned.get('owner')
        if owner and owner.is_superuser:
            self.add_error('owner', 'Süper admin marka sahibi olamaz.')
        if panel_kind == BusinessBrand.PANEL_DEALER and not parent:
            self.add_error('parent_brand', 'Bayi paneli için merkez marka seçin.')
        host_slug = cleaned.get('host_slug', '')
        if host_slug is not None:
            try:
                cleaned['host_slug'] = validate_brand_tenant_key(
                    host_slug,
                    brand=self.instance,
                    panel_kind=panel_kind,
                    parent_brand=parent,
                )
            except ValueError as exc:
                self.add_error('host_slug', str(exc))
        return cleaned


def _plan_module_choices():
    from common.module_catalog import (
        MODULE_KIND_APP,
        MODULE_KIND_INTEGRATION,
        MODULE_STATUS_ACTIVE,
        MODULE_STATUS_BETA,
        MODULES,
    )

    apps = []
    integrations = []
    for mod in MODULES:
        if mod['status'] not in (MODULE_STATUS_ACTIVE, MODULE_STATUS_BETA):
            continue
        if mod['slug'].startswith('agency_') or mod['slug'] == 'settings':
            continue
        if mod['kind'] == MODULE_KIND_INTEGRATION:
            integrations.append((mod['slug'], mod['name']))
        elif mod['kind'] == MODULE_KIND_APP:
            from common.panel_registry import panel_for_module

            panel = panel_for_module(mod['slug'])
            panel_name = panel['name'] if panel else 'Panel'
            apps.append((mod['slug'], f"{panel_name} — {mod['name']}"))
    return apps, integrations


def _plan_particle_choices():
    from common.module_particles import PARTICLES

    return [
        (p['slug'], p['name'])
        for p in PARTICLES
        if p['slug'].startswith('p.') and not p['slug'].startswith('p.agency')
    ]


class AdminPlanForm(forms.ModelForm):
    included_modules = forms.MultipleChoiceField(
        label='Plana dahil modüller',
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    included_integrations = forms.MultipleChoiceField(
        label='Plana dahil entegrasyonlar',
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    included_particles = forms.MultipleChoiceField(
        label='Plana dahil parçacıklar (opsiyonel)',
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        from core_settings.models import Plan

        model = Plan
        fields = [
            'name',
            'price',
            'restaurant_plan_tier',
            'trial_days',
            'billing_days',
            'max_hq_brands',
            'max_dealer_panels',
            'max_users_per_brand',
            'max_customers_per_brand',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT}),
            'price': forms.NumberInput(attrs={'class': INPUT, 'step': '0.01'}),
            'restaurant_plan_tier': forms.Select(
                attrs={'class': INPUT},
                choices=[('', '— Otomatik —'), ('starter', 'Starter'), ('growth', 'Growth'), ('enterprise', 'Enterprise')],
            ),
            'trial_days': forms.NumberInput(attrs={'class': INPUT, 'min': 0}),
            'billing_days': forms.NumberInput(attrs={'class': INPUT, 'min': 1}),
            'max_hq_brands': forms.NumberInput(attrs={'class': INPUT}),
            'max_dealer_panels': forms.NumberInput(attrs={'class': INPUT}),
            'max_users_per_brand': forms.NumberInput(attrs={'class': INPUT}),
            'max_customers_per_brand': forms.NumberInput(attrs={'class': INPUT}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apps, integrations = _plan_module_choices()
        self.fields['included_modules'].choices = apps
        self.fields['included_integrations'].choices = integrations
        self.fields['included_particles'].choices = _plan_particle_choices()
        self.fields['max_hq_brands'].label = 'Maksimum merkez panel'
        self.fields['max_dealer_panels'].label = 'Maksimum bayi alt panel'
        if self.instance and self.instance.pk:
            stored = list(self.instance.included_module_slugs or [])
            self.fields['included_modules'].initial = [
                s for s in stored if s in dict(apps)
            ]
            self.fields['included_integrations'].initial = [
                s for s in stored if s in dict(integrations)
            ]
            self.fields['included_particles'].initial = list(
                self.instance.included_particle_slugs or []
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        modules = self.cleaned_data.get('included_modules', [])
        integrations = self.cleaned_data.get('included_integrations', [])
        instance.included_module_slugs = list(modules) + list(integrations)
        instance.included_particle_slugs = self.cleaned_data.get('included_particles', [])
        if commit:
            instance.save()
        return instance


class AdminBillingInvoiceForm(forms.ModelForm):
    class Meta:
        from core_settings.models import BillingInvoice

        model = BillingInvoice
        fields = ['user', 'plan', 'amount', 'status']
        widgets = {
            'user': forms.Select(attrs={'class': INPUT}),
            'plan': forms.Select(attrs={'class': INPUT}),
            'amount': forms.NumberInput(attrs={'class': INPUT, 'step': '0.01'}),
            'status': forms.Select(attrs={'class': INPUT}),
        }

    def __init__(self, *args, **kwargs):
        from common.brand_team import production_users_queryset
        from core_settings.models import Plan

        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = production_users_queryset().exclude(is_superuser=True).order_by('username')
        self.fields['plan'].queryset = Plan.objects.filter(is_active=True).order_by('price')


class AdminSiteSettingsForm(forms.ModelForm):
    class Meta:
        from core_settings.models import SiteSettings

        model = SiteSettings
        fields = [
            'site_name',
            'logo',
            'company_phone',
            'company_address',
            'currency_code',
            'primary_vertical_slug',
            'ai_chat_enabled',
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={'class': INPUT}),
            'logo': forms.ClearableFileInput(attrs={'class': INPUT}),
            'company_phone': forms.TextInput(attrs={'class': INPUT}),
            'company_address': forms.Textarea(attrs={'class': INPUT, 'rows': 3}),
            'currency_code': forms.Select(attrs={'class': INPUT}),
            'primary_vertical_slug': forms.TextInput(attrs={'class': INPUT}),
            'ai_chat_enabled': forms.CheckboxInput(attrs={'class': CHECKBOX}),
        }
