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

# Track walk logs and reminders by group ID
group_last_walked_time = {}
group_walker_logs = {}

async def walked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    now = datetime.datetime.now()

    group_last_walked_time[chat_id] = now
    user = update.effective_user
    username = user.username or user.first_name

    if chat_id not in group_walker_logs:
        group_walker_logs[chat_id] = {}
    group_walker_logs[chat_id][username] = now

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ Trudy says thank you {user.first_name}!"
    )

async def send_reminder(context: ContextTypes.DEFAULT_TYPE, chat_id):
    now = datetime.datetime.now()
    last_walked = group_last_walked_time.get(chat_id)

    if last_walked and (now - last_walked).total_seconds() < 14400:
        return  # Trudy was walked in the last 4 hours

    await context.bot.send_message(chat_id=chat_id, text="🦮 Someone take Trudy out please")

async def reminder_scheduler(application):
    while True:
        now = datetime.datetime.now()
        if now.hour in [0, 9, 13, 17, 21] and now.minute == 0:
            for chat_id in group_last_walked_time.keys():
                await send_reminder(None, chat_id)
            await asyncio.sleep(60)
        await asyncio.sleep(10)

async def bad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now()
    chat_id = update.effective_chat.id

    try:
        members = await context.bot.get_chat_administrators(chat_id=chat_id)
        all_names = [m.user.username or m.user.first_name for m in members if not m.user.is_bot]

        group_log = group_walker_logs.get(chat_id, {})

        bad_list = [
            name for name in all_names
            if name not in group_log or (now - group_log[name]).total_seconds() > 86400
        ]

        if bad_list:
            bad_str = "Trudy doesn't like these people:\n" + "\n".join(f"- {n}" for n in bad_list)
        else:
            bad_str = "✅ Everyone has been good to Trudy today"

        await context.bot.send_message(chat_id=chat_id, text=bad_str)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Error checking /bad: {e}")

async def post_init(application):
    asyncio.create_task(reminder_scheduler(application))

def main():
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("walked", walked))
    app.add_handler(CommandHandler("bad", bad))
    app.run_polling()

if __name__ == '__main__':
    main()
