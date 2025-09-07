from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 🔹 Replace with your bot token
BOT_TOKEN = "8392213332:AAE8vq4X1GbmuOmmX6Hdix7CUwTvAtb3iQ0"

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("📊 My Salary", callback_data="salary")],
        [InlineKeyboardButton("👥 Invite Friends", callback_data="invite")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        "👋 Welcome to SalaryBot!\n\nChoose an option below:",
        reply_markup=keyboard
    )

# Handle button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "salary":
        await query.edit_message_text("💰 Your current salary is: 0 units")
    elif query.data == "invite":
        await query.edit_message_text("👥 Invite friends using your referral link!")
    elif query.data == "withdraw":
        await query.edit_message_text("💸 Minimum withdrawal is 100 units.")
    elif query.data == "help":
        await query.edit_message_text("ℹ️ This is SalaryBot. Refer friends and earn salary!")

# Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
