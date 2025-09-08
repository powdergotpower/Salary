import json
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.constants import ParseMode

# ---------------- CONFIG ----------------
BOT_TOKEN = "8392213332:AAE8vq4X1GbmuOmmX6Hdix7CUwTvAtb3iQ0"  # <- paste your bot token here
CHANNEL_USERNAME = "@salaryget"
DATA_FILE = "data.json"
REFERRAL_REWARD = 2.5
MIN_WITHDRAW = 100  # coins

# ---------------- DATA ----------------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def ensure_user(user_id, username):
    data = load_data()
    if str(user_id) not in data:
        data[str(user_id)] = {
            "username": username or "",
            "coins": 0.0,
            "referrals": [],
            "referred_by": None,
        }
        save_data(data)
    return data

# ---------------- UI ----------------
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 My Salary", callback_data="salary")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("🏦 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Help / Info", callback_data="info")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])

def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("✅ Done", callback_data="joined")]
    ])

# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or f"User{user.id}"
    data = ensure_user(user_id, username)

    # Referral system
    if context.args:
        ref_id = context.args[0]
        if ref_id != user_id:
            if data[user_id]["referred_by"] is None:
                data[user_id]["referred_by"] = ref_id
                ref_data = ensure_user(ref_id, None)
                data[ref_id]["coins"] += REFERRAL_REWARD
                data[ref_id]["referrals"].append(user_id)
                data[user_id]["coins"] += REFERRAL_REWARD
                save_data(data)
                # Notify referrer
                try:
                    await context.bot.send_message(
                        chat_id=int(ref_id),
                        text=f"🎉 Great news! {username} has joined via your referral.\n\n"
                             f"You earned +{REFERRAL_REWARD} coins (₹{REFERRAL_REWARD}).\n"
                             f"Your new balance: {data[ref_id]['coins']} coins (₹{data[ref_id]['coins']})."
                    )
                except:
                    pass

    welcome_text = (
        f"👋 Welcome *{username}*!\n\n"
        f"📢 This is *SalaryBot*, a professional system where you earn a fixed monthly salary "
        f"by referring people to join our community channel.\n\n"
        f"💰 *How it works:*\n"
        f"- 1 referral = {REFERRAL_REWARD} coins = ₹{REFERRAL_REWARD}\n"
        f"- Coins = Rupees (1 coin = ₹1)\n"
        f"- Salary is paid monthly.\n\n"
        f"✅ To get started, you must join our official channel:"
    )

    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=join_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = str(user.id)
    username = user.username or f"User{user.id}"
    data = ensure_user(user_id, username)

    choice = query.data

    # Force join check
    if choice == "joined":
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
        if member.status in ["member", "administrator", "creator"]:
            await query.edit_message_text("✅ Thank you for joining the channel!\n\nHere is your main menu:",
                                          reply_markup=main_menu())
        else:
            await query.edit_message_text("⚠️ You must join the channel before continuing.",
                                          reply_markup=join_keyboard())
        return

    if choice == "back":
        await query.edit_message_text("🏠 Main Menu:", reply_markup=main_menu())
        return

    if choice == "salary":
        coins = data[user_id]["coins"]
        refs = len(data[user_id]["referrals"])
        text = (
            f"💼 *My Salary Information*\n\n"
            f"👤 Username: @{username}\n"
            f"💰 Current Balance: {coins} coins (₹{coins})\n"
            f"👥 Total Referrals: {refs}\n\n"
            f"📅 Remember: Your salary is calculated monthly and paid out at the end of each month."
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

    elif choice == "refer":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        text = (
            f"👥 *Refer & Earn*\n\n"
            f"Each person who joins using your link and subscribes to our channel will earn *you* "
            f"{REFERRAL_REWARD} coins (₹{REFERRAL_REWARD}) and *them* {REFERRAL_REWARD} coins as a welcome bonus.\n\n"
            f"📌 Your referral link:\n{ref_link}\n\n"
            f"Invite as many as you can — more referrals = higher monthly salary!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

    elif choice == "withdraw":
        coins = data[user_id]["coins"]
        if coins < MIN_WITHDRAW:
            text = (
                f"🏦 *Withdraw Section*\n\n"
                f"⚠️ Your balance is {coins} coins (₹{coins}).\n"
                f"You need at least {MIN_WITHDRAW} coins (₹{MIN_WITHDRAW}) to request a withdrawal.\n\n"
                f"💡 Keep referring friends to increase your monthly salary!"
            )
        else:
            text = (
                f"🏦 *Withdraw Section*\n\n"
                f"✅ Congratulations! You are eligible for withdrawal.\n"
                f"Your current balance: {coins} coins (₹{coins}).\n\n"
                f"📌 Withdrawals are processed monthly. Please contact admin to claim your payout."
            )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

    elif choice == "info":
        text = (
            f"ℹ️ *About SalaryBot*\n\n"
            f"This bot is designed to provide a transparent and fair referral-based salary system.\n\n"
            f"📌 Summary:\n"
            f"- 1 referral = {REFERRAL_REWARD} coins = ₹{REFERRAL_REWARD}\n"
            f"- Salary = Coins (1 coin = ₹1)\n"
            f"- Minimum withdrawal = {MIN_WITHDRAW} coins (₹{MIN_WITHDRAW})\n"
            f"- Salary is paid monthly.\n\n"
            f"Stay active, invite your friends, and grow your monthly salary!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

# ---------------- AUTO LEAVE CHECK ----------------
async def check_leaves(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.my_chat_member:
        return  # ignore bot status updates
    if update.chat_member:
        user = update.chat_member.from_user
        status = update.chat_member.new_chat_member.status
        if status == "left":
            user_id = str(user.id)
            data = load_data()
            if user_id in data and data[user_id]["referred_by"]:
                ref_id = data[user_id]["referred_by"]
                if ref_id in data:
                    data[ref_id]["coins"] -= REFERRAL_REWARD
                    if user_id in data[ref_id]["referrals"]:
                        data[ref_id]["referrals"].remove(user_id)
                    save_data(data)
                    try:
                        await context.bot.send_message(
                            chat_id=int(ref_id),
                            text=f"⚠️ Your referral @{user.username or user_id} has left the channel.\n"
                                 f"-{REFERRAL_REWARD} coins deducted.\n\n"
                                 f"Your new balance: {data[ref_id]['coins']} coins (₹{data[ref_id]['coins']})."
                        )
                    except:
                        pass

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("help", start))  # fallback
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("help", start))

    # Track members joining/leaving
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("help", start))

    print("🤖 SalaryBot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
