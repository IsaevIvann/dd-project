# core/signals.py
import logging
from django.conf import settings
from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail

from .models import Order
from .notify import (
    tg_send_to_admins,
    tg_send_to_order,
    format_admin_new_order,
    format_status_message,
    status_ru,
    format_dt,
    send_once,  # КЭШ + БД-замок (таблица core_notifylock)
)

log = logging.getLogger(__name__)
log.warning("core.signals imported (enhanced)")

# --- email утилита -----------------------------------------------------------

def email_send(subject: str, message: str, to: str):
    if not to:
        return
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [to],
            fail_silently=False,
        )
    except Exception as e:
        log.error("Email send error: %s", e)

# --- создание заказа: 1 TG админу + 1 email клиенту -------------------------

@receiver(post_save, sender=Order, weak=False, dispatch_uid="order_created_once")
def order_created_once(sender, instance: Order, created: bool, **kwargs):
    if not created:
        return

    base = f"notify:order:{instance.pk}:created"

    def _send_admin():
        tg_send_to_admins(format_admin_new_order(instance))

    def _send_client_email():
        body = (
            f"Здравствуйте, {instance.name}!\n\n"
            f"Ваша заявка №{instance.pk} успешно принята.\n\n"
        )
        if instance.pickup_address:
            body += f"Адрес забора: {instance.pickup_address}\n"
        if getattr(instance, "pickup_time", None):
            body += f"Дата/время забора: {format_dt(instance.pickup_time)}\n"
        if instance.delivery_address:
            body += f"Адрес доставки: {instance.delivery_address}\n"
        if getattr(instance, "delivery_time", None):
            body += f"Дата/время доставки: {format_dt(instance.delivery_time)}\n"
        body += "\nСпасибо, что выбрали Drop & Delivery!"
        email_send(f"Заявка №{instance.pk} принята", body, instance.email)

    # триггерим после коммита — и строго по одному разу
    transaction.on_commit(lambda: send_once(base + ":admin", _send_admin))
    transaction.on_commit(lambda: send_once(base + ":email", _send_client_email))

# --- смена статуса: 1 TG админ + 1 TG клиент + 1 email клиент ----------------

@receiver(pre_save, sender=Order, weak=False, dispatch_uid="order_status_changed_once")
def order_status_changed_once(sender, instance: Order, **kwargs):
    if not instance.pk:
        return

    try:
        old_status = sender.objects.only("status").get(pk=instance.pk).status
    except sender.DoesNotExist:
        return

    new_status = instance.status
    if old_status == new_status:
        return

    log.warning("pre_save fired: id=%s %s -> %s", instance.pk, old_status, new_status)

    base = f"notify:order:{instance.pk}:status:{old_status}->{new_status}"

    # 1) TG админам
    transaction.on_commit(lambda: send_once(
        base + ":admin",
        lambda: tg_send_to_admins(format_status_message(instance, old_status))
    ))

    # 2) TG клиенту (если привязан)
    transaction.on_commit(lambda: send_once(
        base + ":client_tg",
        lambda: tg_send_to_order(instance, format_status_message(instance, old_status))
    ))

    # 3) Email клиенту (RU)
    if instance.email:
        old_ru = status_ru(old_status)
        new_ru = status_ru(new_status)

        lines = [
            f"Здравствуйте, {instance.name}!",
            "",
            "Статус вашего заказа изменился:",
            f"{old_ru} → {new_ru}",
            "",
        ]
        if instance.pickup_address:
            lines.append(f"Адрес забора: {instance.pickup_address}")
        if getattr(instance, "pickup_time", None):
            lines.append(f"Дата/время забора: {format_dt(instance.pickup_time)}")
        if instance.delivery_address:
            lines.append(f"Адрес доставки: {instance.delivery_address}")
        if getattr(instance, "delivery_time", None):
            lines.append(f"Дата/время доставки: {format_dt(instance.delivery_time)}")
        lines.append("Спасибо, что выбрали Drop & Delivery!")
        body = "\n".join(lines)

        transaction.on_commit(lambda: send_once(
            base + ":client_email",
            lambda: email_send(f"Заказ №{instance.pk}: статус изменён", body, instance.email)
        ))
