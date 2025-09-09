from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from data_handler import load_data, save_data
from inline_buttons.menu_buttons import main_menu, back_button
from inline_buttons import referral_handler, salary_handler
from config import MIN_WITHDRAW, REFERRAL_REWARD

# ------------------ Callback for inline buttons ------------------ #
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = str(user.id)
    username = user.username or f"User{user.id}"

    # Load all user data
    data_all = load_data()

    # Ensure user exists in data_all and has all necessary keys
    if user_id not in data_all:
        data_all[user_id] = {
            "name": username,
            "salary": 0,
            "coins": 0,
            "joined_channel": False,
            "referred_by": None,
            "referrer_counted": [],
            "referrals": []
        }

    # Make sure old users have missing keys
    user_data = data_all[user_id]
    user_data.setdefault("salary", 0)
    user_data.setdefault("coins", 0)
    user_data.setdefault("joined_channel", False)
    user_data.setdefault("referred_by", None)
    user_data.setdefault("referrer_counted", [])
    user_data.setdefault("referrals", [])

    data = user_data  # Reference to user dict inside data_all
    choice = query.data

    # ------------------ JOINED BUTTON ------------------ #
    if choice == "joined":
        if not data["joined_channel"]:
            data["joined_channel"] = True
            data["salary"] += REFERRAL_REWARD
            data["coins"] = data.get("coins", 0) + REFERRAL_REWARD

            # Notify user
            await query.edit_message_text(
                f"✅ You joined the channel! +{REFERRAL_REWARD} coins added to your salary.",
                parse_mode=ParseMode.MARKDOWN
            )

            # Reward referrer if exists
            ref_id = data.get("referred_by")
            if ref_id:
                if ref_id not in data_all:
                    data_all[ref_id] = {
                        "name": f"User{ref_id}",
                        "salary": 0,
                        "coins": 0,
                        "joined_channel": False,
                        "referred_by": None,
                        "referrer_counted": [],
                        "referrals": []
                    }
                ref_data = data_all[ref_id]
                ref_data.setdefault("salary", 0)
                ref_data.setdefault("coins", 0)
                ref_data.setdefault("referrals", [])

                ref_data["salary"] += REFERRAL_REWARD
                ref_data["coins"] += REFERRAL_REWARD
                ref_data["referrals"].append(user_id)  # Track referral

                # Notify referrer
                try:
                    await context.bot.send_message(
                        chat_id=int(ref_id),
                        text=f"🎉 Your referral @{username} joined the channel! +{REFERRAL_REWARD} coins added to your salary.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except:
                    pass  # In case bot can't message referrer

            # Save updated data
            save_data(data_all)

        # Show main menu
        await query.edit_message_text(
            "🏠 *Main Menu*\n\n"
            "Use the buttons below:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu()
        )
        return

    # ------------------ BACK BUTTON ------------------ #
    if choice == "back":
        await query.edit_message_text(
            "🏠 *Main Menu*\n\n"
            "Use buttons below to navigate:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu()
        )
        return

    # ------------------ SALARY ------------------ #
    if choice == "salary":
        await salary_handler.show_salary(update, context, data, username)
        return

    # ------------------ REFER ------------------ #
    if choice == "refer":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        text = (
            f"👥 *Refer & Earn*\n\nInvite people using your referral link. "
            f"Each person who joins the channel earns you +{REFERRAL_REWARD} coins.\n\n"
            f"📌 Your referral link:\n{ref_link}"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button()
        )
        return

    # ------------------ WITHDRAW ------------------ #
    if choice == "withdraw":
        await salary_handler.withdraw(update, context, data)
        return

    # ------------------ LEADERBOARD ------------------ #
    if choice == "leaderboard":
        top_users = sorted(
            data_all.items(),
            key=lambda x: x[1].get("coins", 0),
            reverse=True
        )[:10]

        text = "🏆 *Top 10 Users*\n\n"
        for i, (uid, udata) in enumerate(top_users, start=1):
            text += f"{i}. {udata.get('name','Unknown')} — {udata.get('coins',0)} coins\n"

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button()
        )
        return

    # ------------------ INFO ------------------ #
    if choice == "info":
        text = (
            f"ℹ️ *About SalaryBot*\n\n"
            f"• 1 referral = {REFERRAL_REWARD} coins\n"
            "• Coins = ₹1 each\n"
            f"• Minimum withdrawal = {MIN_WITHDRAW}\n"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button()
        )
        return


# ------------------ Register callback handler ------------------ #
def get_callback_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(button_handler)
