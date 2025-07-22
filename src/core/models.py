from django.db import models

class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    name = models.CharField("Имя", max_length=100)
    phone = models.CharField("Телефон", max_length=30, blank=True)
    email = models.EmailField("Email", blank=True)
    telegram = models.CharField("Telegram", max_length=100, blank=True)
    whatsapp = models.CharField("WhatsApp", max_length=100, blank=True)
    pickup_address = models.CharField("Адрес забора", max_length=255)
    pickup_time = models.DateTimeField("Время забора")
    delivery_address = models.CharField("Адрес доставки", max_length=255)
    delivery_time = models.DateTimeField("Время доставки")
    comment = models.TextField("Комментарий", blank=True)
    status = models.CharField("Статус", max_length=20, default="new", choices=[
        ("new", "Новая"),
        ("in_progress", "В работе"),
        ("done", "Выполнена"),
    ])

    def __str__(self):
        return f"{self.name} | {self.pickup_address} → {self.delivery_address}"

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ['-created_at']
