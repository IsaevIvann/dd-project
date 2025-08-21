import logging
import requests
from django.conf import settings
from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Order
from django.core.mail import send_mail
from .notify import format_status_message, format_admin_new_order


log = logging.getLogger(__name__)
log.warning("core.signals imported (enhanced)")

# ==== Отправка в Telegram ====
def tg_send(text: str):
    token = settings.TELEGRAM_BOT_TOKEN
    for chat_id in settings.TELEGRAM_CHAT_IDS:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
        except Exception as e:
            log.error("TG send error: %s", e)

# ==== Отправка писем ====
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

# ==== Создание заказа ====
@receiver(post_save, sender=Order, weak=False, dispatch_uid="order_created_email_tg")
def order_created_email_tg(sender, instance: Order, created: bool, **kwargs):
    if created:
        transaction.on_commit(lambda: tg_send(
            f"Новый заказ #{instance.pk}\n"
            f"Имя: {instance.name}\nТелефон: {instance.phone}\n"
            f"Пункт забора: {instance.pickup_address}\n"
            f"Пункт доставки: {instance.delivery_address}"
        ))
        if instance.email:
            transaction.on_commit(lambda: email_send(
                f"Заявка №{instance.pk} принята",
                f"Здравствуйте, {instance.name}!\n\n"
                f"Ваша заявка #{instance.pk} успешно принята. "
                f"Мы свяжемся с вами для уточнения деталей.\n\n"
                f"Спасибо, что выбрали Drop & Delivery!",
                instance.email
            ))

# ==== Изменение статуса ====
@receiver(pre_save, sender=Order, weak=False, dispatch_uid="order_status_changed_pre_save")
def order_status_changed(sender, instance: Order, **kwargs):
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

    transaction.on_commit(lambda: tg_send(
        f"Заказ #{instance.pk}: статус изменён\n<b>{old_status}</b> → <b>{new_status}</b>"
    ))

    if instance.email:
        transaction.on_commit(lambda: email_send(
            f"Заказ №{instance.pk}: статус изменён",
            f"Здравствуйте, {instance.name}!\n\n"
            f"Статус вашего заказа изменился:\n{old_status} → {new_status}\n\n"
            f"Спасибо, что выбрали Drop & Delivery!",
            instance.email
        ))
