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
REFERRAL_REWARD = 2.5  # coins per referral
MIN_WITHDRAW = 100      # minimum coins to withdraw

# ---------------- DATA ----------------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f, indent=4)

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
    if str(user_id) not in data:
        data[str(user_id)] = {
            "name": username or "UNKNOWN",
            "referrals": [],
            "salary": 0,
            "coins": 0,
            "activated": False,
            "referred_by": None
        }
    else:
        # Auto-repair missing fields
        user = data[str(user_id)]
        user.setdefault("name", username or "UNKNOWN")
        user.setdefault("referrals", [])
        user.setdefault("salary", 0)
        user.setdefault("coins", 0)
        user.setdefault("activated", False)
        user.setdefault("referred_by", None)

    save_data(data)
    return data[str(user_id)]

# ---------------- UI ----------------
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 My Salary", callback_data="salary")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("🏦 Withdraw", callback_data="withdraw")],
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
    data = load_data()
    user_data = ensure_user(user_id, username)

    # Referral system
    if context.args:
        ref_id = context.args[0]
        if ref_id != user_id and user_data["referred_by"] is None:
            user_data["referred_by"] = ref_id
            ref_data = ensure_user(ref_id)
            ref_data["coins"] += REFERRAL_REWARD
            ref_data["referrals"].append(user_id)
            user_data["coins"] += REFERRAL_REWARD
            save_data(data)
            # Notify referrer
            try:
                await context.bot.send_message(
                    chat_id=int(ref_id),
                    text=(
                        f"🎉 Congratulations! {username} has joined using your referral link.\n\n"
                        f"You earned +{REFERRAL_REWARD} coins (₹{REFERRAL_REWARD}).\n"
                        f"Your new balance: {ref_data['coins']} coins (₹{ref_data['coins']})."
                    )
                )
            except:
                pass

    # Check if user already joined channel
    member_status = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
    if member_status.status in ["member", "administrator", "creator"]:
        # Already joined → show main menu
        await update.message.reply_text(
            f"👋 Welcome back, *{username}*!\n\n"
            "🏠 You are already a member of our official channel.\n"
            "Use the menu below to manage your salary and referrals.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu()
        )
        return

    # Not joined → show join message
    welcome_text = (
        f"👋 Welcome *{username}*!\n\n"
        "📢 This is *SalaryBot*, a professional referral-based salary system.\n\n"
        "💰 How it works:\n"
        f"- Each referral = +{REFERRAL_REWARD} coins = ₹{REFERRAL_REWARD}\n"
        "- Coins are equivalent to ₹1 per coin.\n"
        "- Salary is calculated monthly and added automatically.\n\n"
        "✅ To start earning, you must join our official channel:"
    )

    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=join_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = str(user.id)
    username = user.username or f"User{user.id}"
    data = load_data()
    user_data = ensure_user(user_id, username)

    choice = query.data

    # ✅ Force join check
    if choice == "joined":
        member_status = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
        if member_status.status in ["member", "administrator", "creator"]:
            await query.edit_message_text(
                "✅ Thank you for joining the channel!\n\nHere is your main menu:",
                reply_markup=main_menu()
            )
        else:
            await query.edit_message_text(
                "⚠️ You must join the channel before continuing.",
                reply_markup=join_keyboard()
            )
        return

    # ⬅️ Back button
    if choice == "back":
        await query.edit_message_text("🏠 Main Menu:", reply_markup=main_menu())
        return

    # 💰 Salary section
    if choice == "salary":
        coins = user_data["coins"]
        refs = len(user_data["referrals"])
        text = (
            f"💼 *My Salary Information*\n\n"
            f"👤 Username: @{username}\n"
            f"💰 Current Balance: {coins} coins (₹{coins})\n"
            f"👥 Total Referrals: {refs}\n\n"
            "📅 Salary is calculated automatically each month based on your referrals.\n"
            "Keep inviting friends to increase your monthly earnings!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    # 👥 Refer section
    if choice == "refer":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        text = (
            "👥 *Refer & Earn*\n\n"
            f"Each new member who joins using your referral link will earn you +{REFERRAL_REWARD} coins (₹{REFERRAL_REWARD}).\n"
            f"They also receive {REFERRAL_REWARD} coins as a welcome bonus.\n\n"
            f"📌 Your referral link:\n{ref_link}\n\n"
            "💡 More referrals = higher monthly salary!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    # 🏦 Withdraw section
    if choice == "withdraw":
        coins = user_data["coins"]
        if coins < MIN_WITHDRAW:
            text = (
                f"🏦 *Withdraw Section*\n\n"
                f"⚠️ Your balance is {coins} coins (₹{coins}).\n"
                f"You need at least {MIN_WITHDRAW} coins to request a withdrawal.\n\n"
                "💡 Keep referring friends to increase your monthly salary!"
            )
        else:
            text = (
                f"🏦 *Withdraw Section*\n\n"
                "✅ Congratulations! You are eligible for withdrawal.\n"
                f"Your current balance: {coins} coins (₹{coins}).\n\n"
                "📌 Withdrawals are processed monthly. Please contact admin to claim your payout."
            )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    # ℹ️ Info section
    if choice == "info":
        text = (
            "ℹ️ *About SalaryBot*\n\n"
            "This bot provides a transparent, fair, and automated referral-based salary system.\n\n"
            f"📌 Summary:\n"
            f"- Each referral = +{REFERRAL_REWARD} coins = ₹{REFERRAL_REWARD}\n"
            "- Coins are equivalent to ₹1 per coin.\n"
            f"- Minimum withdrawal = {MIN_WITHDRAW} coins.\n"
            "- Salary is calculated monthly.\n\n"
            "💡 Stay active, invite friends, and increase your monthly salary!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

# ---------------- AUTO LEAVE CHECK ----------------
async def check_leaves(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.my_chat_member:
        return
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
                            text=(
                                f"⚠️ Your referral @{user.username or user_id} has left the channel.\n"
                                f"-{REFERRAL_REWARD} coins deducted.\n\n"
                                f"Your new balance: {data[ref_id]['coins']} coins (₹{data[ref_id]['coins']})."
                            )
                        )
                    except:
                        pass

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Track leaves
    app.add_handler(CommandHandler("help", start))  # fallback
    
    print("🤖 SalaryBot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
