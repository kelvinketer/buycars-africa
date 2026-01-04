from django import forms

class PaymentForm(forms.Form):
    phone_number = forms.CharField(
        max_length=15, 
        label="M-Pesa Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg', 
            'placeholder': '07XX...',
            'id': 'phoneInput'
        })
    )