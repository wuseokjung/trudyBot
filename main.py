import os
import datetime
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

last_walked_time = None

async def walked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_walked_time
    last_walked_time = datetime.datetime.now()
    user = update.effective_user.first_name
    await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Trudy says thank you {user}")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    global last_walked_time
    now = datetime.datetime.now()
    if last_walked_time and (now - last_walked_time).total_seconds() < 14400:
        return
    await context.bot.send_message(chat_id=CHAT_ID, text="🦮 Someone take Trudy out please")

async def reminder_scheduler(application):
    while True:
        now = datetime.datetime.now()
        if now.hour in [0, 9, 13, 17, 21] and now.minute == 0:
            await send_reminder(application)
            await asyncio.sleep(60)
        await asyncio.sleep(10)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("walked", walked))

    # Start the reminder scheduler
    app.job_queue.run_once(lambda ctx: asyncio.create_task(reminder_scheduler(app)), when=1)

    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
