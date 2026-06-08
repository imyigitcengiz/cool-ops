from django import forms
from django.contrib.auth import get_user_model

from common.app_role_catalog import restaurant_role_choices, validate_restaurant_role_assignment
from common.brand_team import (
    assignable_roles_queryset,
    owned_brands_queryset,
    role_assignable_by_brand_manager,
)
from common.panel_routing import is_restaurant_brand
from core_settings.models import BrandMembership
from users.admin_forms import INPUT, CHECKBOX, AdminUserCreateForm, AdminUserUpdateForm
from users.utils import get_or_create_user_profile

User = get_user_model()


def _brand_needs_restaurant_role(brand) -> bool:
    return bool(brand and is_restaurant_brand(brand))


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
    restaurant_role = forms.ChoiceField(
        label='KobiPOS rolü',
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': INPUT}),
    )

    def __init__(self, manager, *args, **kwargs):
        self.manager = manager
        super().__init__(*args, **kwargs)
        self.fields['role'].label = 'Panel rolü (KobiOPS)'
        self.fields['role'].queryset = assignable_roles_queryset(manager)
        self.fields['brand'].queryset = owned_brands_queryset(manager)
        self.fields['restaurant_role'].choices = restaurant_role_choices(
            include_blank=True,
            assigner_is_superuser=manager.is_superuser,
        )
        self.show_restaurant_role = False

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role and not role_assignable_by_brand_manager(self.manager, role):
            raise forms.ValidationError('Bu rol atanamaz.')
        return role

    def clean(self):
        cleaned = super().clean()
        brand = cleaned.get('brand')
        restaurant_role = cleaned.get('restaurant_role') or ''
        if _brand_needs_restaurant_role(brand):
            if not restaurant_role:
                self.add_error('restaurant_role', 'Restoran paneli için KobiPOS rolü seçin.')
            else:
                ok, err = validate_restaurant_role_assignment(
                    assigner_is_superuser=self.manager.is_superuser,
                    assigner_role='store_owner',
                    new_role=restaurant_role,
                )
                if not ok:
                    self.add_error('restaurant_role', err)
        else:
            cleaned['restaurant_role'] = ''
        return cleaned


class BrandTeamUserUpdateForm(AdminUserUpdateForm):
    brands = forms.ModelMultipleChoiceField(
        label='Paneller',
        queryset=None,
        required=True,
        widget=forms.SelectMultiple(attrs={'class': INPUT, 'size': 4}),
    )
    restaurant_role = forms.ChoiceField(
        label='KobiPOS rolü',
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': INPUT}),
    )

    def __init__(self, manager, *args, **kwargs):
        self.manager = manager
        super().__init__(*args, **kwargs)
        self.fields['role'].label = 'Panel rolü (KobiOPS)'
        self.fields['role'].queryset = assignable_roles_queryset(manager)
        brand_qs = owned_brands_queryset(manager)
        self.fields['brands'].queryset = brand_qs
        self.fields['restaurant_role'].choices = restaurant_role_choices(
            include_blank=True,
            assigner_is_superuser=manager.is_superuser,
        )
        if self.instance and self.instance.pk:
            self.fields['brands'].initial = list(
                BrandMembership.objects.filter(
                    user=self.instance,
                    brand__in=brand_qs,
                ).values_list('brand_id', flat=True)
            )
            profile = getattr(self.instance, 'profile', None)
            if profile and profile.restaurant_role:
                self.fields['restaurant_role'].initial = profile.restaurant_role
        self.show_restaurant_role = any(
            is_restaurant_brand(brand) for brand in brand_qs
        )

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role and not role_assignable_by_brand_manager(self.manager, role):
            raise forms.ValidationError('Bu rol atanamaz.')
        return role

    def clean(self):
        cleaned = super().clean()
        brands = cleaned.get('brands') or []
        restaurant_role = cleaned.get('restaurant_role') or ''
        has_restaurant = any(is_restaurant_brand(brand) for brand in brands)
        if has_restaurant and restaurant_role:
            ok, err = validate_restaurant_role_assignment(
                assigner_is_superuser=self.manager.is_superuser,
                assigner_role='store_owner',
                new_role=restaurant_role,
            )
            if not ok:
                self.add_error('restaurant_role', err)
        elif not has_restaurant:
            cleaned['restaurant_role'] = ''
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=commit)
        restaurant_role = self.cleaned_data.get('restaurant_role') or ''
        brands = list(self.cleaned_data.get('brands') or [])
        restaurant_brand = next((b for b in brands if is_restaurant_brand(b)), None)
        profile = get_or_create_user_profile(user)
        if restaurant_brand and restaurant_role:
            profile.restaurant_brand = restaurant_brand
            profile.restaurant_role = restaurant_role
            profile.save(update_fields=['restaurant_brand', 'restaurant_role'])
        return user
