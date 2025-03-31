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
walker_log = {}  # Dictionary to store {username: last_walk_time}

async def walked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_walked_time
    last_walked_time = datetime.datetime.now()
    user = update.effective_user
    walker_log[user.username or user.first_name] = last_walked_time
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✅ Trudy says thank you {user.first_name}!"
    )

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
            await send_reminder(None)
            await asyncio.sleep(60)
        await asyncio.sleep(10)

async def bad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now()
    try:
        members = await context.bot.get_chat_administrators(chat_id=update.effective_chat.id)
        all_names = [m.user.username or m.user.first_name for m in members if not m.user.is_bot]

        bad_list = [
            name for name in all_names
            if name not in walker_log or (now - walker_log[name]).total_seconds() > 86400
        ]

        if bad_list:
            bad_str = "These people haven't walked Trudy today:\n" + "\n".join(f"- {n}" for n in bad_list)
        else:
            bad_str = "✅ Everyone has been good to Trudy today"

        await context.bot.send_message(chat_id=update.effective_chat.id, text=bad_str)

    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error checking /bad: {e}")

# ✅ Use post_init to safely start background reminder loop
async def post_init(application):
    asyncio.create_task(reminder_scheduler(application))

async def main():
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("walked", walked))
    app.add_handler(CommandHandler("bad", bad))

    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
