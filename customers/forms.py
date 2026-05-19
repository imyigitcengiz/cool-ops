from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'region', 'address', 'location_link', 'contract_date', 'products']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-3 bg-slate-50 border-none rounded-xl focus:ring-2 focus:ring-brand-500'}),
            'phone': forms.TextInput(attrs={'class': 'w-full p-3 bg-slate-50 border-none rounded-xl focus:ring-2 focus:ring-brand-500'}),
            'region': forms.TextInput(attrs={'class': 'w-full p-3 bg-slate-50 border-none rounded-xl focus:ring-2 focus:ring-brand-500'}),
            'address': forms.Textarea(attrs={'class': 'w-full p-3 bg-slate-50 border-none rounded-xl focus:ring-2 focus:ring-brand-500', 'rows': 2}),
            'location_link': forms.URLInput(attrs={'class': 'w-full p-3 bg-slate-50 border-none rounded-xl focus:ring-2 focus:ring-brand-500', 'placeholder': 'Google Maps Konum Linki'}),
            'contract_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-3 bg-slate-50 border-none rounded-xl focus:ring-2 focus:ring-brand-500'}),
            'products': forms.CheckboxSelectMultiple(attrs={'class': 'flex flex-wrap gap-4'}),
        }
