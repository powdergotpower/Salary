from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ChatMemberHandler
from inline_buttons import button_handler
from data_handler import ensure_user, load_data, save_data
from inline_buttons.menu_buttons import main_menu
from config import BOT_TOKEN, CHANNEL_USERNAME, REFERRAL_REWARD


# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or f"User{user_id}"

    data_all = load_data()
    user_data = ensure_user(user_id, username)

    # -------- Handle referral if exists --------
    if context.args:
        ref_id = context.args[0]
        if ref_id != user_id and "referred_by" not in user_data:
            user_data["referred_by"] = ref_id
            ref_data = ensure_user(ref_id, f"User{ref_id}")
            if "referrer_counted" not in ref_data:
                ref_data["referrer_counted"] = []
            if user_id not in ref_data["referrer_counted"]:
                ref_data["referrer_counted"].append(user_id)
            save_data(data_all)

    # -------- Check if user joined channel --------
    member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
    if member.status in ["member", "administrator", "creator"]:
        if not user_data.get("joined_channel"):
            # First time confirmed join
            user_data["joined_channel"] = True

            # Reward new user
            user_data["coins"] += REFERRAL_REWARD

            # Reward referrer if valid
            if "referred_by" in user_data:
                ref_id = user_data["referred_by"]
                ref_data = ensure_user(ref_id, f"User{ref_id}")

                if "referrer_counted" in ref_data and user_id in ref_data["referrer_counted"]:
                    ref_data["coins"] += REFERRAL_REWARD
                    ref_data["referrer_counted"].remove(user_id)

                    # Notify referrer
                    try:
                        await context.bot.send_message(
                            chat_id=ref_id,
                            text=f"🎉 Congrats! @{username} joined via your referral.\n"
                                 f"💰 You earned {REFERRAL_REWARD} coins!"
                        )
                    except Exception:
                        pass

            # Notify new user
            try:
                await update.message.reply_text(
                    f"👋 Welcome {username}!\n\n"
                    f"✅ You earned {REFERRAL_REWARD} coins for joining the channel.\n"
                    f"💼 Start inviting friends to increase your salary!"
                )
            except Exception:
                pass

            save_data(data_all)

        # Show main menu
        await update.message.reply_text(
            "🏠 *Main Menu*\n\n"
            "Use the buttons below to navigate:",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    else:
        # Send professional join prompt
        await button_handler.send_join_prompt(update, context, username)


# ---------------- MAIN FUNCTION ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Command handler
    app.add_handler(CommandHandler("start", start))

    # Inline buttons handler
    app.add_handler(button_handler.get_callback_handler())

    # Track channel leaves
    app.add_handler(ChatMemberHandler(button_handler.check_leaves, ChatMemberHandler.CHAT_MEMBER))

    print("🤖 SalaryBot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
