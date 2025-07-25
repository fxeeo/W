BOT_TOKEN = "7353573625:AAFBKM_aQvcAUhL6NpKAf9tBQKqZR1Acu2k"
import os
import sys
import subprocess
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import time

# Auto-install required packages
for pkg in ["requests", "pyTelegramBotAPI"]:
    try:
        __import__(pkg if pkg != "pyTelegramBotAPI" else "telebot")
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

# Config
CHANNEL_LINK = "https://t.me/Tacticsy"
ADMIN_LINK = "https://t.me/Avesz"

bot = telebot.TeleBot(BOT_TOKEN)

# Per-user reset history
user_histories = {}

# Command menu
def send_command_list(chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Admin", url=ADMIN_LINK))
    bot.send_message(chat_id,
        "*Command Menu*\n\nAvailable commands:\n"
        "/reset <username or email>\n"
        "/bulk <username> <email>\n"
        "/history - Show your reset log\n"
        "/help - Show command usage\n"
        "/ping - Check bot response time",
        reply_markup=markup, parse_mode="Markdown")

# /start
@bot.message_handler(commands=['start'])
def start(msg):
    send_command_list(msg.chat.id)

# /help
@bot.message_handler(commands=['help'])
def help(msg):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Admin", url=ADMIN_LINK))
    bot.send_message(msg.chat.id,
        "Command Usage:\n"
        "/reset <username or email> - Reset one IG account.\n"
        "/bulk <username> <email> - Bulk reset.\n"
        "/history - Show your reset history\n"
        "/ping - Check response time.", reply_markup=markup)

# /ping
@bot.message_handler(commands=['ping'])
def ping(msg):
    start_time = time.time()
    sent = bot.send_message(msg.chat.id, "Pinging...")
    end_time = time.time()
    latency = int((end_time - start_time) * 1000)
    bot.edit_message_text(f"Pong! {latency}ms", msg.chat.id, sent.message_id)

# IG password reset logic
def send_reset(identifier):
    url = "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/"
    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.instagram.com",
        "referer": "https://www.instagram.com/accounts/password/reset/",
        "user-agent": "Mozilla/5.0 (Android)",
        "x-csrftoken": "BbJnjd.Jnw20VyXU0qSsHLV",
        "x-ig-app-id": "1217981644879628",
        "x-requested-with": "XMLHttpRequest"
    }
    data = {"email_or_username": identifier, "flow": "fxcal"}
    try:
        r = requests.post(url, headers=headers, data=data)
        return r.status_code == 200 and r.json().get("status") == "ok"
    except:
        return False

# /reset
@bot.message_handler(commands=['reset'])
def reset(msg):
    args = msg.text.split()
    if len(args) != 2:
        bot.send_message(msg.chat.id, "Usage: /reset <username or email>")
        return

    identifier = args[1]
    ok = send_reset(identifier)
    status = "Successful" if ok else "Failed"
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save to user's history
    user_id = msg.from_user.id
    user_histories.setdefault(user_id, []).append({
        "user": identifier,
        "status": status,
        "time": time_str
    })

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Admin", url=ADMIN_LINK))
    msg_text = (
        "Reset successful. A password reset link has been sent. Please check your Instagram login email to continue."
        if ok else
        "Reset failed. Please try again later. Make sure the information provided is correct."
    )
    bot.send_message(msg.chat.id, msg_text, reply_markup=markup)

# /bulk
@bot.message_handler(commands=['bulk'])
def bulk(msg):
    args = msg.text.split()
    if len(args) < 3:
        bot.send_message(msg.chat.id, "Usage: /bulk <username> <email>")
        return

    user_id = msg.from_user.id
    user_histories.setdefault(user_id, [])

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Admin", url=ADMIN_LINK))
    results = []

    for iden in args[1:]:
        ok = send_reset(iden)
        status = "Successful" if ok else "Failed"
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        user_histories[user_id].append({
            "user": iden,
            "status": status,
            "time": time_str
        })

        results.append(f"{iden}: {status}")

    bot.send_message(msg.chat.id, "\n".join(results), reply_markup=markup)

# /history
@bot.message_handler(commands=['history'])
def history(msg):
    user_id = msg.from_user.id
    history = user_histories.get(user_id, [])

    if not history:
        bot.send_message(msg.chat.id, "Your reset history is empty.")
        return

    lines = []
    for entry in history[-20:][::-1]:  # Show latest 20
        lines.append(
            f"*{entry['user']}*\n"
            f"• {entry['status']}\n"
            f"• {entry['time']}"
        )

    bot.send_message(msg.chat.id, "\n\n".join(lines), parse_mode="Markdown")

# Run the bot
bot.infinity_polling()
