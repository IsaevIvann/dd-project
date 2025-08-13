from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

BOT_TOKEN = "7607165074:AAEjkZ-zhmWmIPfZejVdxdCR-7CZHIfOMAQ"
API_URL = "http://127.0.0.1:8000/api/link_chat/"
API_TOKEN = "secret-123"

def _link(order_id: str, chat_id: int) -> str:
    r = requests.post(API_URL, json={"order_id": order_id, "chat_id": chat_id},
                      headers={"X-TG-TOKEN": API_TOKEN}, timeout=10)
    return "Готово! Вы будете получать уведомления." if r.status_code == 200 else f"Ошибка: {r.status_code} {r.text}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /start order_14
    args = context.args
    if args and len(args) == 1 and args[0].startswith("order_"):
        order_id = args[0].split("order_", 1)[1]
        msg = _link(order_id, update.effective_chat.id)
        await update.message.reply_text(msg)
        return

    await update.message.reply_text("Команды:\n/set_order <order_id>\n/link <phone> [email]")

async def set_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /set_order <order_id>")
        return
    order_id = context.args[0]
    msg = _link(order_id, update.effective_chat.id)
    await update.message.reply_text(msg)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_order", set_order))
    app.run_polling()

if __name__ == "__main__":
    main()
