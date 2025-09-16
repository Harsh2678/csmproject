from django import forms
from cmsproject.models import ShippingInfo
from django.contrib.auth import get_user_model  # Use this for dynamic user model

User = get_user_model()  # Get the custom user model

class ShippingInfoForm(forms.ModelForm):
    class Meta:
        model = ShippingInfo
        fields = [
            'shipping_first_name', 'shipping_last_name', 'shipping_email',
            'shipping_phone_number', 'shipping_address', 'shipping_city',
            'shipping_state', 'shipping_zipcode'
        ]
        widgets = {
            'shipping_first_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'shipping_last_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'shipping_email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'shipping_phone_number': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'inputmode': 'tel'}),
            'shipping_address': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'shipping_city': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'shipping_state': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'shipping_zipcode': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'inputmode': 'numeric'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shipping_email'].error_messages.update({
            'invalid': 'Enter a valid email address.'
        })
        self.fields['shipping_phone_number'].error_messages.update({
            'invalid': 'Enter a valid phone number (7-15 digits, optional +).' 
        })
        self.fields['shipping_zipcode'].error_messages.update({
            'invalid': 'Enter a valid ZIP/Postal code.'
        })
        for name, field in self.fields.items():
            field.error_messages.setdefault('required', 'This field is required.')

    def clean_shipping_phone_number(self):
        value = self.cleaned_data.get('shipping_phone_number', '')
        digits = ''.join(ch for ch in value if ch.isdigit())
        if len(digits) != 10:
            raise forms.ValidationError('Enter a valid 10-digit phone number.')
        return '+' + digits if value.strip().startswith('+') else digits

    def clean_shipping_zipcode(self):
        value = (self.cleaned_data.get('shipping_zipcode') or '').strip()
        if not value.isdigit() or len(value) != 6:
            raise forms.ValidationError("ZIP code must be exactly 6 digits.")
        return value


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User  # Use the custom user model dynamically assigned above
        fields = ["first_name", "last_name", "email", "phone_number"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            raise forms.ValidationError("Email is required.")
        qs = User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email)
        if qs.exists():
            raise forms.ValidationError("This email is already in use.")
        return email
