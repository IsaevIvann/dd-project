import requests
from django.conf import settings
from django.core.mail import send_mail


def _get(setting_name: str, default=None):
    return getattr(settings, setting_name, default)


def notify_telegram_new_order(order):
    """
    Уведомление АДМИНУ в Telegram (в твой приватный чат).
    Настрой TELEGRAM_ADMIN_CHAT_ID в settings.py.
    """
    token = _get("TELEGRAM_BOT_TOKEN", "")
    admin_chat_id = _get("TELEGRAM_ADMIN_CHAT_ID", "")
    if not (token and admin_chat_id):
        return

    text = (
        "📦 <b>Новая заявка</b>\n\n"
        f"Имя: {order.name}\n"
        f"Телефон: {order.phone or '—'}\n"
        f"Email: {order.email or '—'}\n"
        f"Telegram: {order.telegram or '—'}\n"
        f"WhatsApp: {order.whatsapp or '—'}\n"
        f"Забор: {order.pickup_address} ({order.pickup_time or '—'})\n"
        f"Доставка: {order.delivery_address} ({order.delivery_time or '—'})\n"
        f"Комментарий: {order.comment or '—'}"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": admin_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, data=data, timeout=5)
        print("[TG admin] sent:", r.status_code, r.text[:200])
    except Exception as e:
        print(f"[TG admin] send failed: {e}")


def build_telegram_deeplink(order):
    """
    Ссылка на бота с deep‑link параметром (public_token).
    """
    bot_name = _get("TELEGRAM_BOT_NAME", "dropdelivery_admin_bot")
    return f"https://t.me/{bot_name}?start={order.public_token}"


def send_client_email(order):
    """
    Письмо клиенту (консольный backend — вывод в консоль).
    """
    if not order.email:
        return

    subject = "Drop & Delivery — ваша заявка принята"
    text = (
        f"Здравствуйте, {order.name}!\n\n"
        "Мы приняли вашу заявку. В ближайшее время с вами свяжется представитель.\n"
        f"Забор: {order.pickup_address} ({order.pickup_time or '—'})\n"
        f"Доставка: {order.delivery_address} ({order.delivery_time or '—'})\n\n"
        "Получать статусы в Telegram: "
        f"{build_telegram_deeplink(order)}\n\n"
        "— Команда Drop & Delivery"
    )

    try:
        send_mail(
            subject,
            text,
            _get("DEFAULT_FROM_EMAIL", "no-reply@dropdelivery.local"),
            [order.email],
            fail_silently=False,
        )
        print("[MAIL] queued to console backend")
    except Exception as e:
        print("[MAIL] failed:", e)


def notify_client_telegram(order, text):
    """
    Сообщение КЛИЕНТУ в Telegram (если он привязал чат через /start).
    """
    token = _get("TELEGRAM_BOT_TOKEN", "")
    if not (token and order.telegram_chat_id):
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": order.telegram_chat_id, "text": text}
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print("[TG client] send failed:", e)
