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
    send_once,  # БД-идемпотентность
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
@receiver(post_save, sender=Order, weak=False, dispatch_uid="order_created_admin_email")
def order_created_admin_email(sender, instance: Order, created: bool, **kwargs):
    if not created:
        return

    key = f"notify:order:{instance.pk}:created"

    # Админам (TG)
    transaction.on_commit(lambda: send_once(
        key + ":admin_tg",
        lambda: tg_send_to_admins(format_admin_new_order(instance))
    ))

    # Клиенту (email)
    if instance.email:
        body = (
            f"Здравствуйте, {instance.name}!\n\n"
            f"Ваша заявка #{instance.pk} успешно принята. Мы свяжемся с вами для уточнения деталей.\n\n"
            f"{('Адрес забора: ' + instance.pickup_address + '\\n') if instance.pickup_address else ''}"
            f"{('Дата/время забора: ' + format_dt(getattr(instance, 'pickup_time', None)) + '\\n') if getattr(instance, 'pickup_time', None) else ''}"
            f"{('Адрес доставки: ' + instance.delivery_address + '\\n') if instance.delivery_address else ''}"
            f"{('Дата/время доставки: ' + format_dt(getattr(instance, 'delivery_time', None)) + '\\n') if getattr(instance, 'delivery_time', None) else ''}"
            f"\nСпасибо, что выбрали Drop & Delivery!"
        )
        transaction.on_commit(lambda: send_once(
            key + ":client_email",
            lambda: email_send(f"Заявка №{instance.pk} принята", body, instance.email)
        ))


# ---------- Изменение статуса ----------
@receiver(pre_save, sender=Order, weak=False, dispatch_uid="order_status_changed_client")
def order_status_changed_client(sender, instance: Order, **kwargs):
    """ Клиенту (TG и email) """
    if not instance.pk:
        return

    try:
        old_status = sender.objects.only("status").get(pk=instance.pk).status
    except sender.DoesNotExist:
        return

    new_status = instance.status
    if old_status == new_status:
        return

    key = f"notify:order:{instance.pk}:status:{old_status}->{new_status}"

    # TG клиенту
    transaction.on_commit(lambda: send_once(
        key + ":client_tg",
        lambda: send_status_update(instance, old_status)
    ))

    # Email клиенту
    if instance.email:
        old_ru = status_ru(old_status)
        new_ru = status_ru(new_status)
        pickup_line = f"Адрес забора: {instance.pickup_address}\nДата/время забора: {format_dt(getattr(instance, 'pickup_time', None))}\n" if instance.pickup_address else ""
        delivery_line = f"Адрес доставки: {instance.delivery_address}\nДата/время доставки: {format_dt(getattr(instance, 'delivery_time', None))}\n" if instance.delivery_address else ""

        body = (
            f"Здравствуйте, {instance.name}!\n\n"
            f"Статус вашего заказа изменился:\n{old_ru} → {new_ru}\n\n"
            f"{pickup_line}{delivery_line}"
            f"Спасибо, что выбрали Drop & Delivery!"
        )
        transaction.on_commit(lambda: send_once(
            key + ":client_email",
            lambda: email_send(f"Заказ №{instance.pk}: статус изменён", body, instance.email)
        ))


@receiver(post_save, sender=Order, weak=False, dispatch_uid="order_status_changed_admin")
def order_status_changed_admin(sender, instance: Order, created: bool, **kwargs):
    """ Только админу в TG (после сохранения статуса) """
    if created:
        return
    try:
        old_status = instance._old_status
    except AttributeError:
        return

    new_status = instance.status
    if old_status == new_status:
        return

    key = f"notify:order:{instance.pk}:status:{old_status}->{new_status}"

    transaction.on_commit(lambda: send_once(
        key + ":admin_tg",
        lambda: tg_send_to_admins(format_status_message(instance, old_status))
    ))
