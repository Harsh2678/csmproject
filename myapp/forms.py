from django import forms
from cmsproject.models import ShippingInfo


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
        # Customize error messages
        self.fields['shipping_email'].error_messages.update({
            'invalid': 'Enter a valid email address.'
        })
        self.fields['shipping_phone_number'].error_messages.update({
            'invalid': 'Enter a valid phone number (7-15 digits, optional +).' 
        })
        self.fields['shipping_zipcode'].error_messages.update({
            'invalid': 'Enter a valid ZIP/Postal code.'
        })
        # Required message for all fields
        for name, field in self.fields.items():
            field.error_messages.setdefault('required', 'This field is required.')

    def clean_shipping_phone_number(self):
        value = self.cleaned_data.get('shipping_phone_number', '')
        digits = ''.join(ch for ch in value if ch.isdigit())
        # allow leading + by user, but store digits only
        if len(digits) != 10:
            raise forms.ValidationError('Enter a valid 10-digit phone number.')
        return '+' + digits if value.strip().startswith('+') else digits

    def clean_shipping_zipcode(self):
        value = (self.cleaned_data.get('shipping_zipcode') or '').strip()
        if not value.isdigit() or len(value) != 6:
            raise forms.ValidationError("ZIP code must be exactly 6 digits.")
        return value


