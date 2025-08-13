from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    # Переопределяем модельное поле тем же именем, делаем его обязательным
    consent_pdn = forms.BooleanField(
        required=True,
        label="Согласен(а) с обработкой персональных данных",
        error_messages={"required": "Нужно дать согласие на обработку персональных данных."},
    )

    class Meta:
        model = Order
        fields = [
            "name", "phone", "email", "telegram", "whatsapp",
            "pickup_address", "pickup_time",
            "delivery_address", "delivery_time",
            "comment",
            "consent_pdn",  # показываем один чекбокс
        ]
        widgets = {
            "pickup_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "delivery_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "comment": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        # хотя бы один способ связи
        if not (cleaned.get("phone") or cleaned.get("email") or cleaned.get("telegram") or cleaned.get("whatsapp")):
            raise forms.ValidationError(
                "Укажите хотя бы один способ связи: телефон, email, Telegram или WhatsApp."
            )
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        # зафиксируем момент согласия
        obj.set_consent(self.cleaned_data.get("consent"))
        if commit:
            obj.save()
        return obj