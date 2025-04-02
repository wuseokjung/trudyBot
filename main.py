import os
import datetime
import asyncio
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("TOKEN")

group_last_walked_time = {}
group_walker_logs = {}
registered_users = {}

async def walked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    now = datetime.datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    user = update.effective_user
    username = user.username or user.first_name

    group_last_walked_time[chat_id] = now
    if chat_id not in group_walker_logs:
        group_walker_logs[chat_id] = {}
    group_walker_logs[chat_id][username] = now

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Cheers mate @{username}. Did I poo or pee? Everyone's curious 🦮"
    )

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    username = user.username or user.first_name

    if chat_id not in registered_users:
        registered_users[chat_id] = set()

    registered_users[chat_id].add(username)

    if chat_id not in group_last_walked_time:
        group_last_walked_time[chat_id] = None

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Nice to meet u bruh 🐶"
    )

async def send_reminder(bot, chat_id):
    now = datetime.datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    last_walked = group_last_walked_time.get(chat_id)

    if last_walked and (now - last_walked).total_seconds() < 14400:  # 4 hours
        return

    await bot.send_message(chat_id=chat_id, text="Can someone take me out?")

async def reset_logs(bot, chat_id):
    # Reset the walking logs at midnight
    if chat_id in group_walker_logs:
        group_walker_logs[chat_id] = {}
    if chat_id in group_last_walked_time:
        group_last_walked_time[chat_id] = None

async def send_follow_up_reminder(bot, chat_id):
    await bot.send_message(chat_id=chat_id, text="do u guys even care about me 😞")

async def reminder_scheduler(application):
    sent_times = set()
    follow_up_sent = set()
    reminder_hours = [8, 12, 16, 20, 0]

    while True:
        now = datetime.datetime.now(tz=ZoneInfo("America/Los_Angeles"))
        key = (now.hour, now.minute)

        # Regular reminders
        if now.hour in reminder_hours and now.minute == 0 and key not in sent_times:
            for chat_id in group_last_walked_time.keys():
                print(f"Sending reminder at {now.strftime('%H:%M:%S')} to chat {chat_id}")
                await send_reminder(application.bot, chat_id)
                if now.hour == 0:
                    await reset_logs(application.bot, chat_id)
            sent_times.add(key)
        
        # Follow-up check (2 hours after each reminder)
        for reminder_hour in reminder_hours:
            follow_up_hour = (reminder_hour + 2) % 24
            if now.hour == follow_up_hour and now.minute == 0 and (reminder_hour, chat_id) not in follow_up_sent:
                for chat_id in group_last_walked_time.keys():
                    last_walked = group_last_walked_time.get(chat_id)
                    if not last_walked or (now - last_walked).total_seconds() >= 7200:
                        await send_follow_up_reminder(application.bot, chat_id)
                        follow_up_sent.add((reminder_hour, chat_id))

        if now.minute == 1:
            sent_times.clear()
            follow_up_sent = {(h, c) for h, c in follow_up_sent if h != (now.hour - 1) % 24}

        await asyncio.sleep(30)

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    for user in update.message.new_chat_members:
        username = user.username or user.first_name
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"@{username} Use /join to volunteer to walk me! Here's all you need to know:\n/walked - you walked me\n/list - get a list of sigmas and bad people"
        )

async def post_init(application):
    await application.initialize()
    asyncio.create_task(reminder_scheduler(application))

async def list_walkers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    chat_id = update.effective_chat.id
    group_log = group_walker_logs.get(chat_id, {})
    group_registered = registered_users.get(chat_id, set())

    sigmas = [
        name for name, time in group_log.items()
        if (now - time).total_seconds() <= 86400
    ]

    bad_people = [
        name for name in group_registered
        if name not in group_log or (now - group_log[name]).total_seconds() > 86400
    ]

    msg_parts = []
    if sigmas:
        msg_parts.append("well done you sigmas:")
        msg_parts.extend(f"@{name}" for name in sigmas)
        msg_parts.append("")
    
    if bad_people:
        msg_parts.append("👎 bad people:")
        msg_parts.extend(f"@{name}" for name in bad_people)
    
    msg = "\n".join(msg_parts) if msg_parts else "No registered walkers yet. Use /join to start walking me"

    await context.bot.send_message(chat_id=chat_id, text=msg)

def main():
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("walked", walked))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("list", list_walkers))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.run_polling()

if __name__ == '__main__':
    main()
