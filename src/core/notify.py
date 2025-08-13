import requests
from typing import Tuple
from django.conf import settings

def _val(x):
    return x if x else ""

def _join(*parts):
    return "\n".join(p for p in parts if p)

def tg_send(text: str, chat_id: str) -> Tuple[bool, int, str]:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not token or not chat_id:
        return (False, 0, "Missing token or chat_id")
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": str(chat_id), "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=10,
        )
        return (r.ok, r.status_code, r.text)
    except Exception as e:
        return (False, 0, f"Exception: {e}")


def tg_send_to_order(order, text: str) -> Tuple[bool, int, str]:
    chat_id = getattr(order, "telegram_chat_id", None)
    if not chat_id:
        return (False, 0, "Order has no telegram_chat_id")
    return tg_send(text, chat_id)


def format_status_message(order, old_status=None):
    status = getattr(order, "status", "")
    titles = {
        getattr(order.__class__.Status, "CONFIRMED", "CONFIRMED"): "✅ Заказ подтверждён",
        getattr(order.__class__.Status, "PICKED_UP", "PICKED_UP"): "📦 Забрали багаж",
        getattr(order.__class__.Status, "IN_STORAGE", "IN_STORAGE"): "🏬 Багаж на складе",
        getattr(order.__class__.Status, "OUT_FOR_DELIVERY", "OUT_FOR_DELIVERY"): "🚚 В пути на доставку",
        getattr(order.__class__.Status, "DELIVERED", "DELIVERED"): "🎉 Доставлено",
        getattr(order.__class__.Status, "CANCELED", "CANCELED"): "❌ Заказ отменён",
    }
    title = titles.get(status, f"Статус: {status}")
    line_id = f"Заказ #{order.pk}"
    pickup_block = _join(
        f"Адрес забора: {_val(getattr(order, 'pickup_address', ''))}",
        _join(
            f"Дата/время забора: {_val(getattr(order, 'pickup_time', ''))}",
            f"Окно: {_val(getattr(order, 'pickup_time_from', ''))} – {_val(getattr(order, 'pickup_time_to', ''))}",
        ) if (getattr(order, 'pickup_time', None) or getattr(order, 'pickup_time_from', None) or getattr(order, 'pickup_time_to', None)) else "",
    )
    delivery_block = _join(
        f"Адрес доставки: {_val(getattr(order, 'delivery_address', ''))}",
        _join(
            f"Дата/время доставки: {_val(getattr(order, 'delivery_time', ''))}",
            f"Окно: {_val(getattr(order, 'delivery_time_from', ''))} – {_val(getattr(order, 'delivery_time_to', ''))}",
        ) if (getattr(order, 'delivery_time', None) or getattr(order, 'delivery_time_from', None) or getattr(order, 'delivery_time_to', None)) else "",
    )
    status_line = f"<b>{_val(old_status)}</b> → <b>{status}</b>" if old_status is not None and old_status != status else ""
    return _join(title, line_id, status_line, pickup_block, delivery_block)


def send_status_update(order, old_status=None):
    text = format_status_message(order, old_status)
    return tg_send_to_order(order, text)


def send_welcome(order):
    text = _join(
        "👋 Готово! Мы будем присылать обновления по вашему заказу.",
        f"Заказ #{order.pk}",
        _join(
            f"Адрес забора: {_val(getattr(order, 'pickup_address', ''))}",
            f"Адрес доставки: {_val(getattr(order, 'delivery_address', ''))}",
        )
    )
    return tg_send_to_order(order, text)

def tg_send_to_admins(text: str):
    ids = getattr(settings, "TELEGRAM_ADMIN_CHAT_IDS", [])
    ok = True
    for cid in ids:
        r = tg_send(text, str(cid))
        ok = ok and r[0]
    return ok

def build_deeplink_for_order(order_id: int) -> str:
    username = getattr(settings, "TELEGRAM_BOT_USERNAME", "")
    if not username:
        return ""
    return f"https://t.me/{username}?start=order_{order_id}"