import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest

# -----------------------------
# CONFIG
# -----------------------------
BOT_TOKEN = "8392213332:AAE8vq4X1GbmuOmmX6Hdix7CUwTvAtb3iQ0"
ADMIN_ID = 866048927           # Your Telegram ID
CHANNEL_USERNAME = "@salaryget"
DATA_FILE = "data.json"
# -----------------------------

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 My Salary", callback_data="salary")],
        [InlineKeyboardButton("👥 Invite Friends", callback_data="invite")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

def join_done_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"➡ Join {CHANNEL_USERNAME}", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("✅ Done", callback_data="joined_channel")]
    ])

# -----------------------------
# START COMMAND
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    data = load_data()

    # Initialize user if not exists
    if user_id not in data:
        data[user_id] = {"name": user.first_name, "referrals": [], "salary": 0, "activated": False}
        save_data(data)

    # Handle referral
    ref_id = context.args[0] if context.args else None
    if ref_id and ref_id != user_id:
        if ref_id in data:
            data[user_id]["referrer"] = ref_id
            save_data(data)

    welcome_text = (
        f"👋 Hello {user.first_name}!\n\n"
        "Welcome to **SalaryBot**, your personal referral salary manager!\n\n"
        "💡 To get started, you must join our channel first to activate your account.\n"
        "Click the button below to join and then press ✅ Done after joining.\n\n"
        "📌 Everything is managed via buttons — just click and explore!"
    )
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=join_done_keyboard()
    )

# -----------------------------
# BUTTON HANDLER
# -----------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = load_data()

    if user_id not in data:
        data[user_id] = {"name": query.from_user.first_name, "referrals": [], "salary": 0, "activated": False}
        save_data(data)

    # -----------------------------
    # Done button after joining channel
    # -----------------------------
    if query.data == "joined_channel":
        try:
            member = await context.bot.get_chat_member(CHANNEL_USERNAME, query.from_user.id)
            if member.status == "left":
                await query.edit_message_text(
                    f"⚠️ You must join {CHANNEL_USERNAME} first.\nClick the Join button and then press ✅ Done.",
                    reply_markup=join_done_keyboard()
                )
                return
        except BadRequest:
            await query.edit_message_text(
                f"⚠️ You must join {CHANNEL_USERNAME} first.\nClick the Join button and then press ✅ Done.",
                reply_markup=join_done_keyboard()
            )
            return

        # User joined channel → activate account
        if not data[user_id]["activated"]:
            data[user_id]["activated"] = True
            data[user_id]["salary"] = 1  # new user gets 1 salary
            # Add salary to referrer if exists
            ref_id = data[user_id].get("referrer")
            if ref_id and ref_id in data:
                data[ref_id]["salary"] += 1
                if "referrals" not in data[ref_id]:
                    data[ref_id]["referrals"] = []
                if user_id not in data[ref_id]["referrals"]:
                    data[ref_id]["referrals"].append(user_id)
            save_data(data)

        await query.edit_message_text(
            "✅ Congratulations! Your account is now activated and your salary is 1 unit.\n\n"
            "Use the buttons below to explore all features.",
            reply_markup=main_menu_keyboard()
        )
        return

    # -----------------------------
    # Main Menu Buttons
    # -----------------------------
    # Ensure user is activated before accessing features
    if not data[user_id]["activated"]:
        await query.edit_message_text(
            f"⚠️ You must join {CHANNEL_USERNAME} first to use the bot.\nClick the Join button and then press ✅ Done.",
            reply_markup=join_done_keyboard()
        )
        return

    # MY SALARY
    if query.data == "salary":
        salary = data[user_id]["salary"]
        referral_count = len(data[user_id].get("referrals", []))
        text = (
            f"📊 **Your Salary**\n\n"
            f"💰 Current Salary: {salary} units\n"
            f"👥 Referrals: {referral_count}\n\n"
            f"Remember, each friend you invite who joins {CHANNEL_USERNAME} gives you +1 unit!\n"
            "Keep inviting to grow your salary!"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard())

    # INVITE FRIENDS
    elif query.data == "invite":
        referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
        text = (
            "👥 **Invite Friends**\n\n"
            f"Share your personal referral link:\n{referral_link}\n\n"
            f"Each friend who joins {CHANNEL_USERNAME} using your link gives you +1 salary unit.\n"
            "Encourage your friends to join and increase your earnings!"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_keyboard())

    # WITHDRAW
    elif query.data == "withdraw":
        salary = data[user_id]["salary"]
        if salary < 100:
            await query.edit_message_text(
                "⚠️ You need at least 100 units to withdraw.\nKeep inviting friends to reach the minimum!",
                reply_markup=back_keyboard()
            )
        else:
            await query.edit_message_text(
                "✅ Withdrawal request sent to Admin for approval.",
                reply_markup=back_keyboard()
            )
            await context.bot.send_message(
                ADMIN_ID,
                f"💸 Withdrawal request from {data[user_id]['name']} (ID: {user_id})\n"
                f"Salary: {salary} units"
            )

    # HELP
    elif query.data == "help":
        help_text = (
            "ℹ️ **SalaryBot Help**\n\n"
            "1️⃣ **Main Menu Buttons:**\n"
            "- 📊 My Salary – Shows your current salary and referral count.\n"
            "- 👥 Invite Friends – Gives your personal referral link.\n"
            "- 💸 Withdraw – Request withdrawal if you have at least 100 units.\n"
            "- ℹ️ Help – Shows this help text.\n\n"
            "2️⃣ **Referral System:**\n"
            f"- Invite friends to join {CHANNEL_USERNAME}. Each join = +1 salary unit.\n"
            "- Referrer also earns +1 when a friend joins.\n"
            "- Users must join the channel to count.\n\n"
            "3️⃣ **Withdraw Rules:**\n"
            "- Minimum 100 units required.\n"
            "- Admin will approve withdrawals.\n\n"
            "4️⃣ **Navigation:**\n"
            "- Use 🔙 Back button to return to Main Menu."
        )
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=back_keyboard())

    # BACK BUTTON
    elif query.data == "back":
        await query.edit_message_text("📌 **Main Menu:**", parse_mode="Markdown", reply_markup=main_menu_keyboard())

    # Save data after every action
    save_data(data)

# -----------------------------
# MAIN FUNCTION
# -----------------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🤖 Professional SalaryBot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
