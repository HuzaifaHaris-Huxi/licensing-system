from django import forms
from .models import LicenseKey, ClientProfile

class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = ['name', 'email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Customer Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'customer@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+123456789'}),
        }

class LicenseKeyForm(forms.ModelForm):
    class Meta:
        model = LicenseKey
        fields = ['product_name', 'client', 'duration_days', 'grace_period_days']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional Software Name'}),
            'client': forms.Select(attrs={'class': 'form-input'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-input', 'min': '1', 'placeholder': 'e.g. 10'}),
            'grace_period_days': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
        }
