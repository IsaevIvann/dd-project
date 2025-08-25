import logging
import requests
from typing import Tuple
from django.conf import settings
from django.utils.timezone import localtime

log = logging.getLogger(__name__)

# ---------- Вспомогательные утилиты ----------

def _val(x):
    return x if x else ""

def _join(*parts):
    return "\n".join(p for p in parts if p)

def _fmt_dt(dt):
    if not dt:
        return ""
    # локальное время проекта (TIME_ZONE / USE_TZ)
    return localtime(dt).strftime("%d.%m.%Y %H:%M")

def format_dt(dt) -> str:
    """Публичный помощник для форматирования дат в письмах/логах."""
    return _fmt_dt(dt)

def status_ru(value: str) -> str:
    """Маппинг машинных статусов -> русский текст без эмодзи (для e‑mail/логов)."""
    mapping = {
        "draft": "Черновик",
        "confirmed": "Подтверждён",
        "picked_up": "Забрали багаж",
        "in_storage": "На складе",
        "out_for_delivery": "В пути на доставку",
        "delivered": "Доставлено",
        "canceled": "Отменён",
    }
    return mapping.get(value, value)

def _status_title(order, status_value: str) -> str:
    """Титулы со значками (для TG)."""
    S = order.__class__.Status
    titles = {
        S.DRAFT: "📝 Черновик",
        S.CONFIRMED: "✅ Подтверждён",
        S.PICKED_UP: "📦 Забрали багаж",
        S.IN_STORAGE: "🏬 Багаж на складе",
        S.OUT_FOR_DELIVERY: "🚚 В пути на доставку",
        S.DELIVERED: "🎉 Доставлено",
        S.CANCELED: "❌ Отменён",
    }
    return titles.get(status_value, f"Статус: {status_value}")

def _pickup_block(order):
    if not _val(getattr(order, "pickup_address", "")):
        return ""
    return _join(
        f"Адрес забора: {_val(order.pickup_address)}",
        f"Дата/время забора: {_fmt_dt(getattr(order, 'pickup_time', None))}",
    )

def _delivery_block(order):
    if not _val(getattr(order, "delivery_address", "")):
        return ""
    return _join(
        f"Адрес доставки: {_val(order.delivery_address)}",
        f"Дата/время доставки: {_fmt_dt(getattr(order, 'delivery_time', None))}",
    )

# ---------- Отправка в Telegram ----------

def tg_send(text: str, chat_id: str) -> Tuple[bool, int, str]:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not token or not chat_id:
        return (False, 0, "Missing token or chat_id")
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={
                "chat_id": str(chat_id),
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        return (r.ok, r.status_code, r.text)
    except Exception as e:
        return (False, 0, f"Exception: {e}")

def _normalize_chat_ids(ids):
    if ids is None:
        return []
    if isinstance(ids, (str, int)):
        ids = [ids]
    out = []
    for x in ids:
        s = str(x).strip()
        if s:
            out.append(s)
    return list(dict.fromkeys(out))  # dedup c сохранением порядка

def _get_admin_chat_ids():
    # приоритетный одиночный чат
    single = getattr(settings, "ADMIN_TG_CHAT_ID", "")
    if single:
        return _normalize_chat_ids(single)
    # запасной список
    ids = getattr(settings, "TELEGRAM_CHAT_IDS", [])
    return _normalize_chat_ids(ids)

def tg_send_to_admins(text: str):
    ids = _get_admin_chat_ids()
    if not ids:
        log.warning("tg_send_to_admins: no admin chat ids configured (ADMIN_TG_CHAT_ID/TELEGRAM_CHAT_IDS empty)")
        return False
    ok = True
    for cid in ids:
        r = tg_send(text, cid)
        ok = ok and r[0]
        if not r[0]:
            log.error("tg_send_to_admins failed for %s: %s %s", cid, r[1], r[2])
    return ok

def tg_send_to_order(order, text: str) -> Tuple[bool, int, str]:
    chat_id = getattr(order, "telegram_chat_id", None)
    if not chat_id:
        return (False, 0, "Order has no telegram_chat_id")
    return tg_send(text, chat_id)

# ---------- Шаблоны сообщений для TG ----------

def format_status_message(order, old_status=None):
    new_title = _status_title(order, getattr(order, "status", ""))
    line_id = f"Заказ #{order.pk}"

    status_line = ""
    if old_status is not None and old_status != order.status:
        status_line = f"<b>{_status_title(order, old_status)}</b> → <b>{new_title}</b>"

    return _join(
        new_title,
        line_id,
        status_line,
        _pickup_block(order),
        _delivery_block(order),
    )

def send_status_update(order, old_status=None):
    """Клиентский TG при смене статуса (только если привязан чат)."""
    text = format_status_message(order, old_status)
    return tg_send_to_order(order, text)

def send_welcome(order):
    """Клиентское приветствие при привязке чата."""
    text = _join(
        "👋 Готово! Мы будем присылать обновления по вашему заказу.",
        f"Заказ #{order.pk}",
        _pickup_block(order),
        _delivery_block(order),
    )
    return tg_send_to_order(order, text)

def build_deeplink_for_order(order_id: int) -> str:
    username = getattr(settings, "TELEGRAM_BOT_USERNAME", "") or getattr(settings, "TELEGRAM_BOT_NAME", "")
    if not username:
        return ""
    return f"https://t.me/{username}?start=order_{order_id}"

def format_admin_new_order(order):
    """Шаблон 'Новый заказ' для админов в TG."""
    return _join(
        "🆕 Новый заказ",
        f"Заказ #{order.pk}",
        f"Имя: {_val(getattr(order, 'name', ''))}",
        f"Телефон: {_val(getattr(order, 'phone', ''))}",
        _pickup_block(order),
        _delivery_block(order),
    )
