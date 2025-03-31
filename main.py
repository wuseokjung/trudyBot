from telegram.ext import Updater, CommandHandler
import datetime
import threading
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

last_walked_time = None
walked_lock = threading.Lock()

def walked(update, context):
    global last_walked_time
    with walked_lock:
        last_walked_time = datetime.datetime.now()
    user = update.effective_user.first_name
    context.bot.send_message(chat_id=CHAT_ID, text=f"✅ Thanks {user}!")

def send_reminder(context):
    global last_walked_time
    now = datetime.datetime.now()
    with walked_lock:
        if last_walked_time and (now - last_walked_time).total_seconds() < 14400:
            return
    context.bot.send_message(chat_id=CHAT_ID, text="Reminder: Someone walk Trudy please")

def schedule_reminders(updater):
    reminder_hours = [0, 9, 13, 17, 21]  # 12AM, 9AM, 1PM, 5PM, 9PM
    def run():
        while True:
            now = datetime.datetime.now()
            if now.minute == 0:
                for hour in reminder_hours:
                    if now.hour == hour:
                        send_reminder(updater)
                        time.sleep(60)
            time.sleep(10)
    threading.Thread(target=run).start()

if __name__ == '__main__':
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("walked", walked))

    schedule_reminders(updater)
    updater.start_polling()
