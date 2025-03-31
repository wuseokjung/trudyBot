import os
import datetime
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("TOKEN")

# Per-group tracking
group_last_walked_time = {}
group_walker_logs = {}
registered_users = {}

async def walked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    now = datetime.datetime.now()
    user = update.effective_user
    username = user.username or user.first_name

    group_last_walked_time[chat_id] = now
    if chat_id not in group_walker_logs:
        group_walker_logs[chat_id] = {}
    group_walker_logs[chat_id][username] = now

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Trudy thanks you @{username}"
    )

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    username = user.username or user.first_name

    if chat_id not in registered_users:
        registered_users[chat_id] = set()

    registered_users[chat_id].add(username)

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Thanks mate"
    )

async def send_reminder(context: ContextTypes.DEFAULT_TYPE, chat_id):
    now = datetime.datetime.now()
    last_walked = group_last_walked_time.get(chat_id)

    if last_walked and (now - last_walked).total_seconds() < 14400:
        return

    await context.bot.send_message(chat_id=chat_id, text="🦮 Someone take Trudy out please")

async def reminder_scheduler(application):
    while True:
        now = datetime.datetime.now()
        # //if now.hour in [0, 9, 13, 17, 21] and now.minute == 0:
        if now.hour == 3 and now.minute in [17, 18, 19]:  # Test for 3:17am, 3:18am, 3:19am
            for chat_id in group_last_walked_time.keys():
                await send_reminder(None, chat_id)
            await asyncio.sleep(60)
        await asyncio.sleep(10)

async def bruh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now()
    chat_id = update.effective_chat.id
    group_log = group_walker_logs.get(chat_id, {})
    group_registered = registered_users.get(chat_id, set())

    bruh = [
        name for name in group_registered
        if name not in group_log or (now - group_log[name]).total_seconds() > 86400
    ]

    if bruh:
        msg = "Trudy doesn't like you:\n" + "\n".join(f"- @{n}" for n in bruh)
    else:
        msg = "✅ Everyone's been sigma today!"

    await context.bot.send_message(chat_id=chat_id, text=msg)

async def sigma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now()
    chat_id = update.effective_chat.id
    group_log = group_walker_logs.get(chat_id, {})

    sigma_walkers = [
        name for name, time in group_log.items()
        if (now - time).total_seconds() <= 86400
    ]

    if sigma_walkers:
        msg = "Well done you sigma's:\n" + "\n".join(f"- @{n}" for n in sigma_walkers)
    else:
        msg = "Bad day to be Trudy"

    await context.bot.send_message(chat_id=chat_id, text=msg)

# ✅ New: Auto prompt when someone joins the group
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    for user in update.message.new_chat_members:
        username = user.username or user.first_name
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"@{username} Use /join to volunteer to walk Trudy."
        )

async def post_init(application):
    asyncio.create_task(reminder_scheduler(application))

def main():
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("walked", walked))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("bruh", bruh))
    app.add_handler(CommandHandler("sigma", sigma))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.run_polling()

if __name__ == '__main__':
    main()
