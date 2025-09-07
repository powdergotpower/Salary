import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest

# 🔹 Replace with your bot token
BOT_TOKEN = "8392213332:AAE8vq4X1GbmuOmmX6Hdix7CUwTvAtb3iQ0"

# 🔹 Admin Telegram ID
ADMIN_ID = 8032922682 

# 🔹 Channel username
CHANNEL_USERNAME = "@salaryget"

# Data file
DATA_FILE = "data.json"

# Load user data
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Save user data
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Main menu buttons
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 My Salary", callback_data="salary")],
        [InlineKeyboardButton("👥 Invite Friends", callback_data="invite")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ])

# Back button
def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    data = load_data()

    # Initialize user if not exists
    if user_id not in data:
        data[user_id] = {"name": user.first_name, "referrals": [], "salary": 0}
        save_data(data)

    # Handle referral if present
    if context.args:
        ref_id = context.args[0]
        if ref_id != user_id and ref_id in data:
            # Check if user joined channel
            try:
                member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
                if member.status != "left":
                    if user_id not in data[ref_id]["referrals"]:
                        data[ref_id]["referrals"].append(user_id)
                        data[ref_id]["salary"] += 1
                        save_data(data)
            except BadRequest:
                await update.message.reply_text(
                    f"⚠️ Please join {CHANNEL_USERNAME} first to count your referral."
                )

    welcome_text = (
        f"👋 Hello {user.first_name}!\n\n"
        "Welcome to **SalaryBot**, your personal referral salary manager!\n\n"
        "💡 Invite friends to join our channel @salaryget. Each friend who joins using your referral link gives you +1 salary unit!\n\n"
        "💰 Track your earnings, request withdrawals when you have 100+ units, and explore all features using the buttons below.\n\n"
        "📌 Everything is managed via buttons — just click and explore!"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

# Handle button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = load_data()

    if user_id not in data:
        data[user_id] = {"name": query.from_user.first_name, "referrals": [], "salary": 0}
        save_data(data)

    if query.data == "salary":
        # Check if user still in channel
        try:
            member = await context.bot.get_chat_member(CHANNEL_USERNAME, query.from_user.id)
            if member.status == "left":
                # Deduct salary from referrer(s) if needed
                for uid, udata in data.items():
                    if user_id in udata["referrals"] and udata["salary"] > 0:
                        udata["salary"] -= 1
                save_data(data)
                await query.edit_message_text("⚠️ You left the channel. Referrer salary reduced.")
                return
        except BadRequest:
            pass

        salary = data[user_id]["salary"]
        await query.edit_message_text(f"💰 Your current salary: {salary} units", reply_markup=back_keyboard())

    elif query.data == "invite":
        referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(
            f"👥 Invite friends using this link:\n\n{referral_link}\n\n"
            "Each friend who joins the channel gives you +1 salary unit!",
            reply_markup=back_keyboard()
        )

    elif query.data == "withdraw":
        salary = data[user_id]["salary"]
        if salary < 100:
            await query.edit_message_text("⚠️ You need at least 100 units to withdraw.", reply_markup=back_keyboard())
        else:
            await query.edit_message_text("✅ Withdrawal request sent to Admin.", reply_markup=back_keyboard())
            await context.bot.send_message(
                ADMIN_ID,
                f"💸 Withdrawal request from {data[user_id]['name']} (ID: {user_id})\n"
                f"Salary: {salary} units"
            )

    elif query.data == "help":
        help_text = (
            "ℹ️ **SalaryBot Help**\n\n"
            "1️⃣ **Main Menu Buttons:**\n"
            "- 📊 My Salary – Shows your current salary units.\n"
            "- 👥 Invite Friends – Gives your referral link. Friends must join @salaryget to give you +1 unit.\n"
            "- 💸 Withdraw – Request withdrawal if you have at least 100 units. Admin will approve.\n"
            "- ℹ️ Help – Shows this help text.\n\n"
            "2️⃣ **Referral System:**\n"
            "- Share your referral link with friends.\n"
            "- Only joins to @salaryget count.\n"
            "- If a referred friend leaves the channel, your salary decreases by 1.\n\n"
            "3️⃣ **Withdraw Rules:**\n"
            "- Minimum 100 units required.\n"
            "- Withdrawals are sent to Admin.\n\n"
            "4️⃣ **Navigation:**\n"
            "- Every submenu has a 🔙 Back button to return to Main Menu."
        )
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=back_keyboard())

    elif query.data == "back":
        await query.edit_message_text("📌 Main Menu:", reply_markup=main_menu_keyboard())

# Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🤖 SalaryBot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
