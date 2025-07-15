from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from handlers import setup_handlers
from logger import log_error
from db import init_db

init_db()
app = ApplicationBuilder().token(BOT_TOKEN).build()
setup_handlers(app)
app.add_error_handler(log_error)

print("🤖 gg bro! Linguasaurus is running...")
app.run_polling()