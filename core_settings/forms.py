from django import forms

from .color_utils import DEFAULT_HEX
from .models import (
    PriorityOption,
    ProductOption,
    ServiceTypeOption,
    SiteSettings,
    SolutionPartner,
    SolutionPartnerType,
    ServiceTeam,
    ServicePersonnel,
    StatusOption,
    WhatsAppTemplate,
)

INPUT = 'w-full p-3 bg-slate-50 border-none rounded-xl text-sm'


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'logo', 'company_phone', 'company_address',
            'openai_api_key', 'google_api_key', 'ai_chat_enabled', 'ai_system_prompt',
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={'class': INPUT}),
            'company_phone': forms.TextInput(attrs={'class': INPUT}),
            'company_address': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
            'openai_api_key': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'sk-...'}),
            'google_api_key': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'AIza...'}),
            'ai_chat_enabled': forms.CheckboxInput(attrs={'class': 'w-5 h-5 accent-brand-600 rounded'}),
            'ai_system_prompt': forms.Textarea(attrs={'class': INPUT, 'rows': 3}),
        }


class ProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['sidebar_profile_name', 'sidebar_profile_role']
        widgets = {
            'sidebar_profile_name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: Yiğit Cengiz'}),
            'sidebar_profile_role': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: Operasyon Yöneticisi'}),
        }


class ColorOptionForm(forms.ModelForm):
    color = forms.CharField(
        widget=forms.HiddenInput(attrs={'class': 'color-picker-value'}),
        required=True,
    )

    class Meta:
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'İsim'}),
        }

    def __init__(self, *args, default_color='#3b82f6', **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('color') and not self.data:
            self.initial['color'] = default_color


class ServiceTypeOptionForm(forms.ModelForm):
    class Meta:
        model = ServiceTypeOption
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: Montaj'}),
        }


class ProductOptionForm(ColorOptionForm):
    class Meta(ColorOptionForm.Meta):
        model = ProductOption
        fields = ['name', 'color']
        widgets = {
            **ColorOptionForm.Meta.widgets,
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: Pergola'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, default_color=DEFAULT_HEX['product'], **kwargs)


class StatusOptionForm(ColorOptionForm):
    class Meta(ColorOptionForm.Meta):
        model = StatusOption
        widgets = {
            **ColorOptionForm.Meta.widgets,
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: Servis'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, default_color=DEFAULT_HEX['status'], **kwargs)


class PriorityOptionForm(ColorOptionForm):
    class Meta(ColorOptionForm.Meta):
        model = PriorityOption
        widgets = {
            **ColorOptionForm.Meta.widgets,
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: Acil'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, default_color=DEFAULT_HEX['priority'], **kwargs)


class WhatsAppTemplateForm(forms.ModelForm):
    class Meta:
        model = WhatsAppTemplate
        fields = ['title', 'message']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full p-2 bg-slate-50 border-none rounded-xl text-sm', 'placeholder': 'Örn: Servis Tamamlandı'}),
            'message': forms.Textarea(attrs={'class': 'w-full p-2 bg-slate-50 border-none rounded-xl text-sm', 'rows': 2, 'placeholder': 'Mesaj metni...'}),
        }


class SolutionPartnerForm(forms.ModelForm):
    class Meta:
        model = SolutionPartner
        fields = ['name', 'partner_type', 'phone', 'notes', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: ABC Taşeron'}),
            'partner_type': forms.Select(attrs={'class': INPUT}),
            'phone': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: +90...'}),
            'notes': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: Vinçli araç'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 accent-brand-600 rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['partner_type'].queryset = SolutionPartnerType.objects.order_by('name')
        self.fields['partner_type'].empty_label = 'Tür seçin'


class SolutionPartnerTypeForm(forms.ModelForm):
    class Meta:
        model = SolutionPartnerType
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: Taşeron Firma'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 accent-brand-600 rounded'}),
        }


class ServiceTeamForm(forms.ModelForm):
    class Meta:
        model = ServiceTeam
        fields = ['name', 'product_groups', 'company_phone', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: Mobil Ekip 1'}),
            'product_groups': forms.SelectMultiple(attrs={'class': INPUT, 'size': 6}),
            'company_phone': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: +9053...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 accent-brand-600 rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product_groups'].queryset = ProductOption.objects.order_by('name')


class ServicePersonnelForm(forms.ModelForm):
    class Meta:
        model = ServicePersonnel
        fields = ['name', 'team', 'product_groups', 'company_phone', 'notes', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: Ahmet Usta'}),
            'team': forms.Select(attrs={'class': INPUT}),
            'product_groups': forms.SelectMultiple(attrs={'class': INPUT, 'size': 6}),
            'company_phone': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: +9053...'}),
            'notes': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Örn: Vinç uzmanı'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 accent-brand-600 rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['team'].queryset = ServiceTeam.objects.filter(is_active=True).order_by('name')
        self.fields['team'].empty_label = 'Ekip seçin'
        self.fields['product_groups'].queryset = ProductOption.objects.order_by('name')


