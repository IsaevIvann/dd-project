from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'name', 'phone', 'email', 'telegram', 'whatsapp',
            'pickup_address', 'pickup_time', 'delivery_address', 'delivery_time', 'comment'
        ]
        widgets = {
            'pickup_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'delivery_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Валидация: хотя бы один способ связи
        if not (
            cleaned_data.get('phone') or
            cleaned_data.get('email') or
            cleaned_data.get('telegram') or
            cleaned_data.get('whatsapp')
        ):
            raise forms.ValidationError(
                "Укажите хотя бы один способ связи: телефон, email, Telegram или WhatsApp."
            )
        return cleaned_data
