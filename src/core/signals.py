import logging
from django.conf import settings
from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail

from .models import Order
from .notify import (
    tg_send_to_admins,
    format_admin_new_order,
    format_status_message,
    send_status_update,
    status_ru,
    format_dt,
    send_once,
)

log = logging.getLogger(__name__)
log.warning("core.signals imported (enhanced)")

# ---------- Email ----------

def email_send(subject: str, message: str, to: str):
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

# ---------- Создание заказа ----------

@receiver(post_save, sender=Order, weak=False, dispatch_uid="order_created_admin_email_v2")
def order_created_admin_email(sender, instance: Order, created: bool, **kwargs):
    if not created:
        return

    # ключ для антидубля (на случай двойного импорта сигналов/нескольких воркеров)
    dedup_key = f"notify:order:{instance.pk}:created"

    def _send_admin():
        tg_send_to_admins(format_admin_new_order(instance))

    def _send_client_email():
        if not instance.email:
            return
        body = (
            f"Здравствуйте, {instance.name}!\n\n"
            f"Ваша заявка #{instance.pk} успешно принята. Мы свяжемся с вами для уточнения деталей.\n\n"
            f"{('Адрес забора: ' + instance.pickup_address + '\\n') if instance.pickup_address else ''}"
            f"{('Дата/время забора: ' + format_dt(getattr(instance, 'pickup_time', None)) + '\\n') if getattr(instance, 'pickup_time', None) else ''}"
            f"{('Адрес доставки: ' + instance.delivery_address + '\\n') if instance.delivery_address else ''}"
            f"{('Дата/время доставки: ' + format_dt(getattr(instance, 'delivery_time', None)) + '\\n') if getattr(instance, 'delivery_time', None) else ''}"
            f"\nСпасибо, что выбрали Drop & Delivery!"
        )
        email_send(f"Заявка №{instance.pk} принята", body, instance.email)

    transaction.on_commit(lambda: send_once(dedup_key + ":admins", _send_admin))
    transaction.on_commit(lambda: send_once(dedup_key + ":client_email", _send_client_email))

# ---------- Изменение статуса ----------

@receiver(pre_save, sender=Order, weak=False, dispatch_uid="order_status_changed_both_v2")
def order_status_changed_both(sender, instance: Order, **kwargs):
    # только для существующих заявок
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

    dedup_base = f"notify:order:{instance.pk}:status:{old_status}->{new_status}"

    # TG админам
    transaction.on_commit(lambda: send_once(
        dedup_base + ":admins",
        lambda: tg_send_to_admins(format_status_message(instance, old_status))
    ))

    # TG клиенту (если привязан чат)
    transaction.on_commit(lambda: send_once(
        dedup_base + ":client_tg",
        lambda: send_status_update(instance, old_status)
    ))

    # Email клиенту — с русскими статусами
    if instance.email:
        old_ru = status_ru(old_status)
        new_ru = status_ru(new_status)

        pickup_line = ""
        if getattr(instance, "pickup_address", ""):
            pickup_line = (
                f"Адрес забора: {instance.pickup_address}\n"
                f"Дата/время забора: {format_dt(getattr(instance, 'pickup_time', None))}\n"
            )

        delivery_line = ""
        if getattr(instance, "delivery_address", ""):
            delivery_line = (
                f"Адрес доставки: {instance.delivery_address}\n"
                f"Дата/время доставки: {format_dt(getattr(instance, 'delivery_time', None))}\n"
            )

        body = (
            f"Здравствуйте, {instance.name}!\n\n"
            f"Статус вашего заказа изменился:\n{old_ru} → {new_ru}\n\n"
            f"{pickup_line}{delivery_line}"
            f"Спасибо, что выбрали Drop & Delivery!"
        )

        transaction.on_commit(lambda: send_once(
            dedup_base + ":client_email",
            lambda: email_send(f"Заказ №{instance.pk}: статус изменён", body, instance.email)
        ))
