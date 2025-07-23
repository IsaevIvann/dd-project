import requests

TELEGRAM_TOKEN = "7607165074:AAEjkZ-zhmWmIPfZejVdxdCR-7CZHIfOMAQ"  # (твой токен)
TELEGRAM_CHAT_ID = "191742166"

def notify_telegram_new_order(order):
    text = (
        f"📦 <b>Новая заявка</b>\n\n"
        f"Имя: {order.name}\n"
        f"Телефон: {order.phone or '—'}\n"
        f"Email: {order.email or '—'}\n"
        f"Telegram: {order.telegram or '—'}\n"
        f"WhatsApp: {order.whatsapp or '—'}\n"
        f"Забор: {order.pickup_address} ({order.pickup_time})\n"
        f"Доставка: {order.delivery_address} ({order.delivery_time})\n"
        f"Комментарий: {order.comment or '—'}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"[TG] Ошибка отправки: {e}")
