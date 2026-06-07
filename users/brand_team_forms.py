from django import forms
from django.contrib.auth import get_user_model

from common.brand_team import (
    assignable_roles_queryset,
    owned_brands_queryset,
    role_assignable_by_brand_manager,
)
from core_settings.models import BrandMembership
from users.admin_forms import INPUT, CHECKBOX, AdminUserCreateForm, AdminUserUpdateForm

User = get_user_model()


class BrandTeamUserCreateForm(AdminUserCreateForm):
    brand = forms.ModelChoiceField(
        label='Panel',
        queryset=None,
        widget=forms.Select(attrs={'class': INPUT}),
    )
    membership_role = forms.ChoiceField(
        label='Panel üyeliği',
        choices=(
            (BrandMembership.ROLE_MEMBER, 'Ekip üyesi'),
            (BrandMembership.ROLE_DEALER, 'Bayi kullanıcısı'),
        ),
        widget=forms.Select(attrs={'class': INPUT}),
    )
    is_default_brand = forms.BooleanField(
        label='Varsayılan panel',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': CHECKBOX}),
    )

    def __init__(self, manager, *args, **kwargs):
        self.manager = manager
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = assignable_roles_queryset(manager)
        self.fields['brand'].queryset = owned_brands_queryset(manager)

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role and not role_assignable_by_brand_manager(self.manager, role):
            raise forms.ValidationError('Bu rol atanamaz.')
        return role


class BrandTeamUserUpdateForm(AdminUserUpdateForm):
    brands = forms.ModelMultipleChoiceField(
        label='Paneller',
        queryset=None,
        required=True,
        widget=forms.SelectMultiple(attrs={'class': INPUT, 'size': 4}),
    )

    def __init__(self, manager, *args, **kwargs):
        self.manager = manager
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = assignable_roles_queryset(manager)
        brand_qs = owned_brands_queryset(manager)
        self.fields['brands'].queryset = brand_qs
        if self.instance and self.instance.pk:
            self.fields['brands'].initial = list(
                BrandMembership.objects.filter(
                    user=self.instance,
                    brand__in=brand_qs,
                ).values_list('brand_id', flat=True)
            )

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role and not role_assignable_by_brand_manager(self.manager, role):
            raise forms.ValidationError('Bu rol atanamaz.')
        return role
