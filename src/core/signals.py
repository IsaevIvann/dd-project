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
    send_status_update,  # <- клиентский TG
)

log = logging.getLogger(__name__)
log.warning("core.signals imported (enhanced)")

# ==== E-mail ====
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
@receiver(post_save, sender=Order, weak=False, dispatch_uid="order_created_admin_email")
def order_created_admin_email(sender, instance: Order, created: bool, **kwargs):
    if not created:
        return

    # TG админам — после успешного коммита
    transaction.on_commit(lambda: tg_send_to_admins(format_admin_new_order(instance)))

    # Письмо клиенту (если указан email)
    if instance.email:
        transaction.on_commit(lambda: email_send(
            f"Заявка №{instance.pk} принята",
            (
                f"Здравствуйте, {instance.name}!\n\n"
                f"Ваша заявка #{instance.pk} успешно принята. "
                f"Мы свяжемся с вами для уточнения деталей.\n\n"
                f"Спасибо, что выбрали Drop & Delivery!"
            ),
            instance.email
        ))

# ==== Изменение статуса ====
@receiver(pre_save, sender=Order, weak=False, dispatch_uid="order_status_changed_both")
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

    # TG админам — единый шаблон (русские статусы, красивые даты)
    transaction.on_commit(lambda: tg_send_to_admins(format_status_message(instance, old_status)))

    # TG клиенту — если есть привязанный чат (send_status_update сам проверит chat_id)
    transaction.on_commit(lambda: send_status_update(instance, old_status))

    # Письмо клиенту (оставляем как есть; можно позже локализовать статусы в тексте)
    if instance.email:
        transaction.on_commit(lambda: email_send(
            f"Заказ №{instance.pk}: статус изменён",
            (
                f"Здравствуйте, {instance.name}!\n\n"
                f"Статус вашего заказа изменился:\n{old_status} → {new_status}\n\n"
                f"Спасибо, что выбрали Drop & Delivery!"
            ),
            instance.email
        ))
