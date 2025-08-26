import logging
from django.contrib import admin
from django.db import transaction
from .models import Order

logger = logging.getLogger(__name__)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "created_at", "status",
        "name", "phone", "items_count",
        "pickup_address", "delivery_address",
        "consent", "consent_at",
        "telegram_chat_id",
    )
    list_filter = ("status", "created_at", "consent")
    search_fields = ("id", "name", "phone", "email", "pickup_address", "delivery_address")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at", "consent_ts")
    autocomplete_fields = ()
    list_per_page = 50

    fieldsets = (
        ("Клиент", {
            "fields": (("name", "phone"), ("email", "telegram", "whatsapp"), "telegram_chat_id")
        }),
        ("Логистика", {
            "fields": (
                "items_count",
                "pickup_address",
                ("pickup_time", "pickup_time_from", "pickup_time_to"),
                "delivery_address",
                ("delivery_time", "delivery_time_from", "delivery_time_to"),
            )
        }),
        ("Фиксация", {"fields": ("seal_numbers", "photos")}),
        ("Статус и служебные", {
            "fields": (("status", "promo_code"), "comment", ("consent_pdn", "consent_ts"),
                       ("created_at", "updated_at"))
        }),
    )

    actions = [
        "mark_confirmed", "mark_picked_up", "mark_in_storage",
        "mark_out_for_delivery", "mark_delivered", "mark_canceled",
    ]

    # ВАЖНО: не рассылаем уведомления из админки — это делает сигнал.
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    # ==== Массовые действия ====
    def _bulk_status_change(self, request, qs, new_status):
        # Без своих уведомлений; сигнал сам отправит после фиксации транзакции.
        for obj in qs:
            old = obj.status
            if old == new_status:
                continue
            obj.status = new_status
            obj.save(update_fields=["status"])

    @admin.action(description="Статус → Подтверждён")
    def mark_confirmed(self, request, qs):
        self._bulk_status_change(request, qs, Order.Status.CONFIRMED)

    @admin.action(description="Статус → Забрали")
    def mark_picked_up(self, request, qs):
        self._bulk_status_change(request, qs, Order.Status.PICKED_UP)

    @admin.action(description="Статус → На складе")
    def mark_in_storage(self, request, qs):
        self._bulk_status_change(request, qs, Order.Status.IN_STORAGE)

    @admin.action(description="Статус → В пути на доставку")
    def mark_out_for_delivery(self, request, qs):
        self._bulk_status_change(request, qs, Order.Status.OUT_FOR_DELIVERY)

    @admin.action(description="Статус → Доставлено")
    def mark_delivered(self, request, qs):
        self._bulk_status_change(request, qs, Order.Status.DELIVERED)

    @admin.action(description="Статус → Отменён")
    def mark_canceled(self, request, qs):
        self._bulk_status_change(request, qs, Order.Status.CANCELED)
