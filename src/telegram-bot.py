import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from scraper import get_menu as scrape_menu
import json
import os
from dotenv import load_dotenv
from datetime import time, datetime

USERS_FILE = "users.json"
SENT_MENUS_FILE = "sent_menus.json"
USERS_CAMPUS_FILE = "users_campus.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []

def load_users_campus():
    if os.path.exists(USERS_CAMPUS_FILE):
        with open(USERS_CAMPUS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_users_campus(users_campus):
    with open(USERS_CAMPUS_FILE, 'w') as f:
        json.dump(users_campus, f)

def get_user_campus(chat_id):
    users_campus = load_users_campus()
    for user in users_campus:
        if user.get("chat_id") == chat_id:
            return user.get("campus", "GOIABEIRAS")
    return "GOIABEIRAS"

def set_user_campus(chat_id, campus):
    users_campus = load_users_campus()
    
    # Find existing user and update
    for user in users_campus:
        if user.get("chat_id") == chat_id:
            user["campus"] = campus
            save_users_campus(users_campus)
            return
    
    # Add new user if not found
    users_campus.append({"chat_id": chat_id, "campus": campus})
    save_users_campus(users_campus)

def save_user(chat_id):
    users = load_users()
    if chat_id not in users:
        users.append(chat_id)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)

def change_user_campus_to_alegre(chat_id):
    set_user_campus(chat_id, "ALEGRE")

def load_sent_menus():
    if os.path.exists(SENT_MENUS_FILE):
        with open(SENT_MENUS_FILE, 'r') as f:
            return json.load(f)
    return {"date": "", "lunch_sent": False, "dinner_sent": False}

def save_sent_menus(data):
    with open(SENT_MENUS_FILE, 'w') as f:
        json.dump(data, f)

def reset_daily_status():
    today = datetime.now().strftime("%Y-%m-%d")
    sent_data = load_sent_menus()
    
    if sent_data["date"] != today:
        sent_data = {"date": today, "lunch_sent": False, "dinner_sent": False}
        save_sent_menus(sent_data)
    
    return sent_data

async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    users = load_users()

    if chat_id in users:
        users.remove(chat_id)
        message = "You have been unsubscribed from daily notifications."
    else:
        users.append(chat_id)
        message = "You have been subscribed to daily notifications."

    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

    await update.message.reply_text(message)

async def set_campus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if not context.args or len(context.args) == 0:
        current_campus = get_user_campus(chat_id)
        await update.message.reply_text(
            f"Current campus: {current_campus}\n\n"
            "Usage: /setcamp <campus>\n"
            "Available campuses: GOIABEIRAS, ALEGRE"
        )
        return
    
    campus = context.args[0].upper()
    
    if campus not in ["GOIABEIRAS", "ALEGRE"]:
        await update.message.reply_text(
            "Invalid campus! Available options:\n"
            "- GOIABEIRAS\n"
            "- ALEGRE"
        )
        return
    
    set_user_campus(chat_id, campus)
    await update.message.reply_text(f"Campus set to {campus}! 🎓")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "Welcome to Cardapio RU Ufes Bot!\n\n"
        "Commands:\n"
        "/menu - Get today's menu\n"
        "/almoco - Get today's lunch menu\n"
        "/janta - Get today's dinner menu\n"
        "/notify - Toggle daily notifications\n"
        "/setcamp (GOIABEIRAS, ALEGRE) - Set R.U campus (GOIABEIRAS by default)\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Available commands:\n"
        "/menu - Get today's menu\n"
        "/almoco - Get today's lunch menu\n"
        "/janta - Get today's dinner menu\n"
        "/notify - Toggle daily notifications (ON by default)\n"
        "/setcamp (GOIABEIRAS, ALEGRE) - Set R.U campus (GOIABEIRAS by default)\n"
        "/help - Show this help message\n\n"
        "You can also just type 'menu' and I'll understand!"
    )
    await update.message.reply_text(help_text)

async def get_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id)
    campus = get_user_campus(update.effective_chat.id)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    menu = scrape_menu(campus)
    
    await update.message.reply_text(menu, parse_mode='Markdown')

def __get_lunch(campus="GOIABEIRAS"):
    menu = scrape_menu(campus)
    print(menu)
    if 'Almoço' not in menu and 'ALMOÇO' not in menu:
        return None
    
    lunch_menu = menu.split('Jantar')[0].strip()
    return lunch_menu

async def get_lunch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id)
    campus = get_user_campus(update.effective_chat.id)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    lunch_menu = __get_lunch(campus)
    
    if lunch_menu is None:
        await update.message.reply_text("Lunch menu not available for today yet.")
    else:
        await update.message.reply_text(lunch_menu, parse_mode='Markdown')

def __get_dinner(campus="GOIABEIRAS"):
    menu = scrape_menu(campus)

    if 'Jantar' not in menu:
        return None
    
    dinner_menu = menu.split('Jantar')[1].strip()
    return dinner_menu

async def get_dinner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id)
    campus = get_user_campus(update.effective_chat.id)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    dinner_menu = __get_dinner(campus)
    
    if dinner_menu is None:
        await update.message.reply_text("Dinner menu not available for today yet.")
    else:
        await update.message.reply_text(dinner_menu, parse_mode='Markdown')

async def check_and_send_lunch(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    current_hour = now.hour
    
    # only check between 8 AM and 1 PM (13:00)
    if current_hour < 8 or current_hour >= 13:
        return
    
    if now.weekday() >= 5:
        return
    
    sent_data = reset_daily_status()
    
    if sent_data["lunch_sent"]:
        return
    
    users = load_users()
    sent_count = 0
    
    for chat_id in users:
        try:
            campus = get_user_campus(chat_id)
            lunch_menu = __get_lunch(campus)
            
            if lunch_menu is None:
                continue
            
            message = f"🍽️ Bom dia estudante! Olha aqui o seu delicioso almoço ({campus}):\n\n{lunch_menu}"
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
            sent_count += 1
        except Exception as e:
            print(f"Failed to send lunch to {chat_id}: {e}")
    
    sent_data["lunch_sent"] = True
    save_sent_menus(sent_data)
    
    print(f"[{now.strftime('%H:%M')}] Lunch menu sent to {sent_count} users")

async def check_and_send_dinner(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    current_hour = now.hour
    
    # only check between 2 PM (14:00) and 7 PM (19:00)
    if current_hour < 14 or current_hour >= 19:
        return
    
    if now.weekday() >= 5:
        return
    
    sent_data = reset_daily_status()
    
    if sent_data["dinner_sent"]:
        return
    
    users = load_users()
    sent_count = 0
    
    for chat_id in users:
        try:
            campus = get_user_campus(chat_id)
            dinner_menu = __get_dinner(campus)
            
            if dinner_menu is None:
                continue
            
            message = f"Boa tarde estudante! Da uma olhada na sua jantinha ({campus}):\n\n{dinner_menu}"
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
            sent_count += 1
        except Exception as e:
            print(f"Failed to send dinner to {chat_id}: {e}")
    
    sent_data["dinner_sent"] = True
    save_sent_menus(sent_data)
    
    print(f"[{now.strftime('%H:%M')}] Dinner menu sent to {sent_count} users")

async def periodic_menu_check(context: ContextTypes.DEFAULT_TYPE):
    await check_and_send_lunch(context)
    await check_and_send_dinner(context)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id)

    text = update.message.text.lower()
    
    if any(word in text for word in ['menu', 'cardapio', 'cardápio']):
        await get_menu(update, context)
    elif any(word in text for word in ['almoco', 'almosso', 'almoço']):
        await get_lunch(update, context)
    elif any(word in text for word in ['janta', 'jantar', 'jantinha']):
        await get_dinner(update, context)
    else:
        await update.message.reply_text(
            "Hi! I can help you get the Ufes menu for today. Type /menu or just say 'menu'!"
        )

def main():
    load_dotenv()
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not set!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", get_menu))
    application.add_handler(CommandHandler("almoco", get_lunch))
    application.add_handler(CommandHandler("janta", get_dinner))
    application.add_handler(CommandHandler("notify", toggle_notifications))
    application.add_handler(CommandHandler("setcamp", set_campus))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    job_queue = application.job_queue
    job_queue.run_repeating(
        periodic_menu_check,
        interval=600,  # 600 seconds = 10 minutes
        first=10,  # start checking 10 seconds after bot starts
        name="menu_checker"
    )
    
    print("Bot is starting...")
    print("Will check for lunch menu every 10 minutes from 8 AM to 2 PM")
    print("Will check for dinner menu every 10 minutes from 2 PM to 8 PM")
    print("Only on weekdays (Monday to Friday)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    main()
