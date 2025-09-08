from telegram.ext import Application, ChatMemberHandler
from inline_buttons import button_handler
from data_handler import ensure_user, load_data, save_data
from inline_buttons.menu_buttons import main_menu
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

BOT_TOKEN = "8392213332:AAE8vq4X1GbmuOmmX6Hdix7CUwTvAtb3iQ0"
CHANNEL_USERNAME = "@salaryget"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or f"User{user.id}"
    data = ensure_user(user_id, username)

    # Check if user joined channel
    if not data.get("joined_channel", False):
        await button_handler.send_join_prompt(update, context, username)
    else:
        await update.message.reply_text("🏠 Main Menu:", reply_markup=main_menu())

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Start handler
    app.add_handler(CommandHandler("start", start))
    
    # Inline buttons
    app.add_handler(button_handler.get_callback_handler())

    # Track channel leaves
    app.add_handler(ChatMemberHandler(button_handler.check_leaves, ChatMemberHandler.CHAT_MEMBER))

    print("🤖 SalaryBot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
