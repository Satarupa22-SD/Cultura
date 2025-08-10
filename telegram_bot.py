import os
from dotenv import load_dotenv
load_dotenv()
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gemini_utils import handle_telegram_message

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm Cultura, your AI style & culture companion.\nJust send me a message about skincare, outfits, events, or travel, and I'll give you vibe-aligned suggestions!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    user_id = str(update.message.from_user.id)
    try:
        reply = handle_telegram_message(user_msg, user_id)
    except Exception as e:
        reply = f"Sorry, there was an error: {e}"
    await update.message.reply_text(reply)

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set in .env")
        exit(1)
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Cultura Telegram bot is running...")
    app.run_polling() 