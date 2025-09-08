import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes, ChatMemberHandler
)
from telegram.constants import ParseMode

# ---------------- CONFIG ----------------
BOT_TOKEN = "8392213332:AAE8vq4X1GbmuOmmX6Hdix7CUwTvAtb3iQ0"  # Your bot token
CHANNEL_USERNAME = "@salaryget"
DATA_FILE = "data.json"
REFERRAL_REWARD = 2.5
MIN_WITHDRAW = 100  # Minimum coins to withdraw

# ---------------- DATA HANDLING ----------------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f, indent=4)

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def ensure_user(user_id, username=None):
    """Ensure the user exists in data with all required fields."""
    data = load_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {
            "name": username or "UNKNOWN",
            "referrals": [],
            "salary": 0,
            "coins": 0,
            "activated": False,
            "referred_by": None,
            "joined_channel": False
        }
    else:
        user = data[user_id]
        # Auto-repair missing fields
        user.setdefault("name", username or "UNKNOWN")
        user.setdefault("referrals", [])
        user.setdefault("salary", 0)
        user.setdefault("coins", 0)
        user.setdefault("activated", False)
        user.setdefault("referred_by", None)
        user.setdefault("joined_channel", False)
    save_data(data)
    return data[user_id]

# ---------------- UI ----------------
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 My Salary", callback_data="salary")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("🏦 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📊 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("ℹ️ Info / Help", callback_data="info")],
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
    
    # Handle referrals if /start <ref_id>
    if context.args:
        ref_id = context.args[0]
        if ref_id != user_id and data.get("referred_by") is None:
            data["referred_by"] = ref_id
            ref_data = ensure_user(ref_id)
            ref_data["coins"] += REFERRAL_REWARD
            ref_data["referrals"].append(user_id)
            data["coins"] += REFERRAL_REWARD
            save_data(load_data())
            try:
                await context.bot.send_message(
                    chat_id=int(ref_id),
                    text=(
                        f"🎉 {username} joined using your referral link!\n"
                        f"You earned +{REFERRAL_REWARD} coins.\n"
                        f"New balance: {ref_data['coins']} coins."
                    )
                )
            except:
                pass

    # Check if user has already joined the channel
    if not data.get("joined_channel", False):
        welcome_text = (
            f"👋 Welcome *{username}*!\n\n"
            f"📢 This is *SalaryBot*, a professional referral-based system where you earn a monthly salary.\n\n"
            f"💰 *How it works:*\n"
            f"- 1 referral = {REFERRAL_REWARD} coins (₹{REFERRAL_REWARD})\n"
            f"- Salary is calculated monthly.\n"
            f"- Coins = Rupees (1 coin = ₹1)\n\n"
            f"✅ To start, join our official channel:"
        )
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=join_keyboard())
    else:
        await update.message.reply_text("🏠 Main Menu:", reply_markup=main_menu())

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
            data["joined_channel"] = True
            save_data(load_data())
            await query.edit_message_text("✅ Thank you for joining the channel!\n\nMain Menu:", reply_markup=main_menu())
        else:
            await query.edit_message_text("⚠️ You must join the channel before continuing.", reply_markup=join_keyboard())
        return

    if choice == "back":
        await query.edit_message_text("🏠 Main Menu:", reply_markup=main_menu())
        return

    if choice == "salary":
        coins = data["coins"]
        refs = len(data["referrals"])
        text = (
            f"💼 *My Salary Information*\n\n"
            f"👤 Username: @{username}\n"
            f"💰 Current Balance: {coins} coins (₹{coins})\n"
            f"👥 Total Referrals: {refs}\n\n"
            f"📅 Salary is calculated monthly based on your referrals."
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

    elif choice == "refer":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        text = (
            f"👥 *Refer & Earn*\n\n"
            f"Invite people using your referral link. Each person who joins and subscribes to our channel earns you +{REFERRAL_REWARD} coins.\n\n"
            f"📌 Your referral link:\n{ref_link}"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

    elif choice == "withdraw":
        coins = data["coins"]
        if coins < MIN_WITHDRAW:
            text = (
                f"🏦 *Withdraw Section*\n\n"
                f"⚠️ Your balance: {coins} coins.\n"
                f"You need at least {MIN_WITHDRAW} coins to withdraw.\n"
                f"Keep referring friends to increase your monthly salary."
            )
        else:
            text = (
                f"🏦 *Withdraw Section*\n\n"
                f"✅ Eligible for withdrawal!\n"
                f"Balance: {coins} coins.\n"
                f"📌 Contact admin to claim your payout."
            )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

    elif choice == "leaderboard":
        data_all = load_data()
        top_users = sorted(data_all.items(), key=lambda x: x[1].get("coins",0), reverse=True)[:10]
        text = "🏆 *Top 10 Users*\n\n"
        for i, (uid, udata) in enumerate(top_users, start=1):
            text += f"{i}. {udata.get('name','Unknown')} — {udata.get('coins',0)} coins\n"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

    elif choice == "info":
        text = (
            f"ℹ️ *About SalaryBot*\n\n"
            f"SalaryBot is a professional referral-based salary system.\n"
            f"Invite friends, earn coins, and get monthly payouts.\n\n"
            f"📌 Rules:\n"
            f"- 1 referral = {REFERRAL_REWARD} coins = ₹{REFERRAL_REWARD}\n"
            f"- Coins = Rupees (1 coin = ₹1)\n"
            f"- Minimum withdrawal = {MIN_WITHDRAW} coins\n"
            f"- Salary is calculated monthly\n"
            f"Stay active, invite friends, and grow your earnings!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

# ---------------- AUTO LEAVE CHECK ----------------
async def check_leaves(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Triggered when a member leaves the channel/group.
    Deduct coins from the referrer if their referred user leaves.
    """
    if update.chat_member:
        user = update.chat_member.from_user
        status = update.chat_member.new_chat_member.status
        user_id = str(user.id)
        data_all = load_data()

        # Only process if user left
        if status == "left":
            if user_id in data_all and data_all[user_id].get("referred_by"):
                ref_id = data_all[user_id]["referred_by"]
                if ref_id in data_all:
                    # Deduct referral reward
                    data_all[ref_id]["coins"] -= REFERRAL_REWARD
                    if user_id in data_all[ref_id]["referrals"]:
                        data_all[ref_id]["referrals"].remove(user_id)
                    save_data(data_all)
                    try:
                        await context.bot.send_message(
                            chat_id=int(ref_id),
                            text=(
                                f"⚠️ Your referral @{user.username or user_id} has left the channel.\n"
                                f"-{REFERRAL_REWARD} coins deducted.\n"
                                f"New balance: {data_all[ref_id]['coins']} coins."
                            )
                        )
                    except:
                        pass

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))

    # CallbackQuery handler
    app.add_handler(CallbackQueryHandler(button_handler))

    # Track leaves
    app.add_handler(ChatMemberHandler(check_leaves, chat_member_types=["member", "left"]))

    print("🤖 SalaryBot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
