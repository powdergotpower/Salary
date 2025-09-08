from telegram import Update
from telegram.ext import Application, CommandHandler, ChatMemberHandler, ContextTypes
from inline_buttons import button_handler
from inline_buttons.menu_buttons import main_menu
from data_handler import ensure_user, load_data, save_data
from config import BOT_TOKEN, CHANNEL_USERNAME

# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or f"User{user.id}"
    data = ensure_user(user_id, username)

    # ---------------- REFERRAL CHECK ----------------
    args = context.args
    if args:
        referrer_id = args[0]
        if referrer_id != user_id and user_id not in data.get("referrer_counted", []):
            ref_data = ensure_user(referrer_id)
            ref_data["coins"] += button_handler.REFERRAL_REWARD
            save_data(load_data())
            data.setdefault("referrer_counted", []).append(user_id)
            save_data(load_data())

    # ---------------- CHANNEL JOIN CHECK ----------------
    member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
    if member.status in ["member", "administrator", "creator"]:
        data["joined_channel"] = True
        save_data(load_data())
        await show_main_menu(update, context, user_id, username)
    else:
        await button_handler.send_join_prompt(update, context, username)

# ---------------- SHOW PROFESSIONAL MAIN MENU ----------------
async def show_main_menu(update, context, user_id, username):
    text = f"🏠 *Welcome {username} to SalaryBot!* \n\n" \
           f"💰 Check your salary, referrals, leaderboard, and more using the buttons below.\n" \
           f"📌 Your coins = ₹{ensure_user(user_id)['coins']}"
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())

# ---------------- MAIN FUNCTION ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Start command
    app.add_handler(CommandHandler("start", start))

    # Inline buttons
    app.add_handler(button_handler.get_callback_handler())

    # Track channel leaves
    app.add_handler(ChatMemberHandler(button_handler.check_leaves, ChatMemberHandler.CHAT_MEMBER))

    print("🤖 SalaryBot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
