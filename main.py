# main.py

from telegram import Update
from telegram.ext import Application, CommandHandler, ChatMemberHandler, ContextTypes
from config import BOT_TOKEN, CHANNEL_USERNAME
from data_handler import ensure_user, load_data, save_data
from inline_buttons import button_handler

# ---------------- START COMMAND ----------------
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
            ref_data["coins"] += button_handler.REFERRAL_REWARD
            ref_data["referrals"].append(user_id)
            data["coins"] += button_handler.REFERRAL_REWARD
            save_data(load_data())
            try:
                await context.bot.send_message(
                    chat_id=int(ref_id),
                    text=(
                        f"🎉 {username} joined using your referral link!\n"
                        f"You earned +{button_handler.REFERRAL_REWARD} coins.\n"
                        f"New balance: {ref_data['coins']} coins."
                    )
                )
            except:
                pass

    # Check if user has already joined the channel
    if not data.get("joined_channel", False):
        # Send professional join prompt from button_handler.py
        await button_handler.send_join_prompt(update, context, username)
    else:
        # Show main menu directly
        await update.message.reply_text("🏠 Main Menu:", reply_markup=button_handler.main_menu())

# ---------------- MAIN FUNCTION ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Start command
    app.add_handler(CommandHandler("start", start))

    # Inline buttons
    app.add_handler(button_handler.get_callback_handler())

    # Track channel leaves (optional)
    app.add_handler(ChatMemberHandler(button_handler.check_leaves, ChatMemberHandler.CHAT_MEMBER))

    print("🤖 SalaryBot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
