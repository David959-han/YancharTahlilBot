import logging
import threading
from flask import Flask
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from config import TELEGRAM_BOT_TOKEN
from bot.handlers import (
    start_handler, help_handler, top_command_handler,
    coin_command_handler, callback_handler, message_handler,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Replit uxlab qolmasligi uchun mini web server
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "YancharBot ishlayapti ✅"

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN .env faylida topilmadi!")

    # Flask ni alohida threadda ishga tushirish
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("top", top_command_handler))
    app.add_handler(CommandHandler("coin", coin_command_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("YancharBot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
