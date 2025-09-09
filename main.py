from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ChatMemberHandler
from inline_buttons import button_handler, referral_handler
from data_handler import ensure_user, load_data, save_data
from inline_buttons.menu_buttons import main_menu
from config import BOT_TOKEN, CHANNEL_LINK, CHANNEL_USERNAME


# /start handler
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
                # only mark them for later verification
                ref_data["referrer_counted"].append(user_id)

    save_data(data_all)

    # -------- Check if user joined channel --------
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)  # Membership check
        if member.status in ["member", "administrator", "creator"]:
            user_data["joined_channel"] = True
            save_data(data_all)
            await update.message.reply_text(
                "🏠 *Main Menu*\n\n"
                "Welcome back! Use the buttons below to navigate:",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        else:
            # Send join prompt
            await referral_handler.send_join_prompt(update, context, username)
    except Exception as e:
        # If something goes wrong (bot not admin or channel invalid)
        print(f"Error checking membership: {e}")
        await referral_handler.send_join_prompt(update, context, username)
