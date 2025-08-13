import uuid

from django.db import models
from django.utils import timezone


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        CONFIRMED = "confirmed", "Подтверждён"
        PICKED_UP = "picked_up", "Забрали"
        IN_STORAGE = "in_storage", "На складе"
        OUT_FOR_DELIVERY = "out_for_delivery", "В пути к доставке"
        DELIVERED = "delivered", "Доставлено"
        CANCELED = "canceled", "Отменён"


    # Клиент
    name = models.CharField("Имя", max_length=120)
    phone = models.CharField("Телефон", max_length=32)
    email = models.EmailField("E‑mail", blank=True)
    telegram = models.CharField("Telegram", max_length=64, blank=True)
    whatsapp = models.CharField("WhatsApp", max_length=64, blank=True)

    # Логистика
    pickup_address = models.CharField("Адрес забора", max_length=255)
    pickup_time = models.DateTimeField("Время забора", null=True, blank=True)  # старое поле — не ломаем формы
    pickup_time_from = models.DateTimeField("Окно забора: с", null=True, blank=True)
    pickup_time_to = models.DateTimeField("Окно забора: до", null=True, blank=True)

    delivery_address = models.CharField("Адрес доставки", max_length=255)
    delivery_time = models.DateTimeField("Время доставки", null=True, blank=True)  # старое поле — не ломаем формы
    delivery_time_from = models.DateTimeField("Окно доставки: с", null=True, blank=True)
    delivery_time_to = models.DateTimeField("Окно доставки: до", null=True, blank=True)

    items_count = models.PositiveSmallIntegerField("Единиц багажа", default=1)
    seal_numbers = models.JSONField("№ пломб (список)", default=list, blank=True)
    photos = models.JSONField("Фото (URL/путь)", default=list, blank=True)

    promo_code = models.CharField("Промокод", max_length=32, blank=True)

    consent_pdn = models.BooleanField("Согласие на ПДн", default=False)
    consent_ts = models.DateTimeField("Время согласия", null=True, blank=True)
    consent_ip = models.GenericIPAddressField("IP при согласии", null=True, blank=True)
    consent_ua = models.CharField("User‑Agent при согласии", max_length=256, blank=True)

    created_at = models.DateTimeField("Создано", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    consent = models.BooleanField(default=False, help_text="Согласие на обработку ПДн")
    consent_at = models.DateTimeField(null=True, blank=True)


    # Состояние/служебное
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    comment = models.TextField("Комментарий", blank=True)

    public_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    telegram_chat_id = models.CharField(max_length=32, blank=True, null=True)



    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ("-created_at",)

    def __str__(self):
        return f"#{self.id} {self.name} — {self.pickup_address} → {self.delivery_address}"

    # Утилита: безопасная смена статуса (на будущее)
    def set_status(self, new_status: str, save: bool = True):
        self.status = new_status
        if save:
            self.save(update_fields=["status", "updated_at"])

    def save(self, *args, **kwargs):
        # автопроставим время согласия, если чекбокс выставлен
        if self.consent_pdn and not self.consent_ts:
            self.consent_ts = timezone.now()
        super().save(*args, **kwargs)


    def set_consent(self, value: bool):
        self.consent = bool(value)
        self.consent_at = timezone.now() if self.consent else None




