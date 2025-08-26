import logging
import threading
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

# ---------- utils: неблокирующая отправка ----------
def _spawn(fn, *args, **kwargs):
    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start()

def _send_mail(subject: str, message: str, to_email: str):
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            fail_silently=False,
        )
    except Exception as e:
        log.error("Email send error: %s", e)

def email_send_async(subject: str, message: str, to_email: str):
    # вызываем в отдельном потоке, чтобы не держать HTTP-запрос
    _spawn(_send_mail, subject, message, to_email)

# ---------- Создание заказа ----------
@receiver(post_save, sender=Order, weak=False, dispatch_uid="order_created_once")
def order_created_once(sender, instance: Order, created: bool, **kwargs):
    if not created:
        return

    key_base = f"notify:order:{instance.pk}:created"

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
        email_send_async(f"Заявка №{instance.pk} принята", body, instance.email)

    transaction.on_commit(lambda: send_once(key_base + ":admins", _send_admin))
    transaction.on_commit(lambda: send_once(key_base + ":client_email", _send_client_email))

# ---------- Изменение статуса ----------
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
    key_base = f"notify:order:{instance.pk}:status:{old_status}->{new_status}"

    # TG админам
    transaction.on_commit(lambda: send_once(
        key_base + ":admins",
        lambda: tg_send_to_admins(format_status_message(instance, old_status))
    ))
    # TG клиенту
    transaction.on_commit(lambda: send_once(
        key_base + ":client_tg",
        lambda: send_status_update(instance, old_status)
    ))
    # Email клиенту (RU)
    if instance.email:
        def _mail():
            old_ru, new_ru = status_ru(old_status), status_ru(new_status)
            pickup = (
                f"Адрес забора: {instance.pickup_address}\n"
                f"Дата/время забора: {format_dt(getattr(instance, 'pickup_time', None))}\n"
            ) if getattr(instance, "pickup_address", "") else ""
            delivery = (
                f"Адрес доставки: {instance.delivery_address}\n"
                f"Дата/время доставки: {format_dt(getattr(instance, 'delivery_time', None))}\n"
            ) if getattr(instance, "delivery_address", "") else ""
            body = (
                f"Здравствуйте, {instance.name}!\n\n"
                f"Статус вашего заказа изменился:\n{old_ru} → {new_ru}\n\n"
                f"{pickup}{delivery}"
                f"Спасибо, что выбрали Drop & Delivery!"
            )
            email_send_async(f"Заказ №{instance.pk}: статус изменён", body, instance.email)

        transaction.on_commit(lambda: send_once(key_base + ":client_email", _mail))
