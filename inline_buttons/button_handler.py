from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from data_handler import load_data, save_data
from inline_buttons.menu_buttons import main_menu, back_button
from config import REFERRAL_REWARD
from inline_buttons import salary_handler

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = str(user.id)
    username = user.username or f"User{user.id}"

    # Load all user data
    data_all = load_data()

    # Ensure user exists
    if user_id not in data_all:
        data_all[user_id] = {
            "name": username,
            "salary": 0,
            "joined_channel": False,
            "referred_by": None,
            "referrer_counted": []
        }

    user_data = data_all[user_id]
    user_data.setdefault("salary", 0)
    user_data.setdefault("joined_channel", False)
    user_data.setdefault("referred_by", None)
    user_data.setdefault("referrer_counted", [])

    choice = query.data

    # ------------------ JOINED BUTTON ------------------ #
    if choice == "joined":
        if not user_data["joined_channel"]:
            user_data["joined_channel"] = True
            user_data["salary"] += REFERRAL_REWARD

            # Notify user
            await context.bot.send_message(
                chat_id=user.id,
                text=f"✅ You joined the channel!\n💰 Your salary increased by {REFERRAL_REWARD} coins."
            )

            # Reward referrer if exists
            ref_id = user_data.get("referred_by")
            if ref_id:
                if ref_id not in data_all:
                    data_all[ref_id] = {
                        "name": f"User{ref_id}",
                        "salary": 0,
                        "joined_channel": False,
                        "referred_by": None,
                        "referrer_counted": []
                    }
                ref_data = data_all[ref_id]
                ref_data.setdefault("salary", 0)
                ref_data["salary"] += REFERRAL_REWARD

                # Notify referrer
                await context.bot.send_message(
                    chat_id=int(ref_id),
                    text=f"💡 Your referral @{username} joined the channel!\n💰 You earned {REFERRAL_REWARD} coins."
                )

            save_data(data_all)

        # Show main menu
        await query.edit_message_text(
            "🏠 *Main Menu*\n\n"
            "You successfully joined! Use the buttons below:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu()
        )
        return

    # ------------------ OTHER BUTTONS ------------------ #
    if choice == "back":
        await query.edit_message_text(
            "🏠 *Main Menu*\n\nUse buttons below to navigate:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu()
        )
        return

    if choice == "salary":
        await salary_handler.show_salary(update, context, user_data, username)
        return
