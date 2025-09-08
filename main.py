import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# ---------------- CONFIG ----------------
BOT_TOKEN = "8392213332:AAE8vq4X1GbmuOmmX6Hdix7CUwTvAtb3iQ0"
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
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def ensure_user(user_id, username=None):
    data = load_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {
            "name": username or "UNKNOWN",
            "referrals": [],
            "salary": 0,
            "coins": 0,
            "activated": False,
            "referred_by": None
        }
    else:
        user = data[user_id]
        user.setdefault("name", username or "UNKNOWN")
        user.setdefault("referrals", [])
        user.setdefault("salary", 0)
        user.setdefault("coins", 0)
        user.setdefault("activated", False)
        user.setdefault("referred_by", None)
    save_data(data)
    return data[user_id]

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
            if data["referred_by"] is None:
                data["referred_by"] = ref_id
                ref_data = ensure_user(ref_id)
                ref_data["coins"] += REFERRAL_REWARD
                ref_data["referrals"].append(user_id)
                data["coins"] += REFERRAL_REWARD
                save_data(load_data())
                try:
                    await context.bot.send_message(
                        chat_id=int(ref_id),
                        text=f"🎉 {username} joined via your referral!\n"
                             f"You earned +{REFERRAL_REWARD} coins.\n"
                             f"New balance: {ref_data['coins']} coins"
                    )
                except:
                    pass

    welcome_text = (
        f"👋 Welcome *{username}*!\n\n"
        f"📢 SalaryBot: earn monthly salary by referrals.\n\n"
        f"💰 How it works:\n"
        f"- 1 referral = {REFERRAL_REWARD} coins (₹{REFERRAL_REWARD})\n"
        f"- Coins = Rupees (1 coin = ₹1)\n"
        f"- Monthly salary\n\n"
        f"✅ Join our channel to start earning:"
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

    if choice == "joined":
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
        if member.status in ["member", "administrator", "creator"]:
            await query.edit_message_text("✅ Joined! Main menu:", reply_markup=main_menu())
        else:
            await query.edit_message_text("⚠️ Join the channel first.", reply_markup=join_keyboard())
        return

    if choice == "back":
        await query.edit_message_text("🏠 Main Menu:", reply_markup=main_menu())
        return

    if choice == "salary":
        coins = data["coins"]
        refs = len(data["referrals"])
        text = (
            f"💼 My Salary\n\n"
            f"👤 @{username}\n"
            f"💰 Balance: {coins} coins\n"
            f"👥 Referrals: {refs}\n"
            f"📅 Paid monthly"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

    elif choice == "refer":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        text = f"👥 Refer & Earn\nYour referral link:\n{ref_link}\nEarn {REFERRAL_REWARD} coins per referral."
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

    elif choice == "withdraw":
        coins = data["coins"]
        if coins < MIN_WITHDRAW:
            text = f"⚠️ Balance {coins} coins. Minimum {MIN_WITHDRAW} required."
        else:
            text = f"✅ Eligible for withdrawal. Balance: {coins} coins."
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

    elif choice == "info":
        text = (
            f"ℹ️ About SalaryBot\n"
            f"1 referral = {REFERRAL_REWARD} coins\n"
            f"Minimum withdrawal = {MIN_WITHDRAW} coins\n"
            f"Paid monthly."
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

# ---------------- AUTO LEAVE CHECK ----------------
async def check_leaves(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                            text=f"⚠️ Referral @{user.username or user_id} left.\n"
                                 f"-{REFERRAL_REWARD} coins.\n"
                                 f"New balance: {data[ref_id]['coins']} coins."
                        )
                    except:
                        pass

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(check_leaves))
    print("🤖 SalaryBot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
