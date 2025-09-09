from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from data_handler import load_data, save_data, ensure_user
from inline_buttons.menu_buttons import main_menu, back_button
from inline_buttons import referral_handler, salary_handler
from config import MIN_WITHDRAW, REFERRAL_REWARD

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = str(user.id)
    username = user.username or f"User{user.id}"

    # Load all data
    data_all = load_data()
    data = ensure_user(user_id, username)  # Safe now, has all keys

    choice = query.data

    if choice == "joined":
        if not data["joined_channel"]:
            data["joined_channel"] = True
            data["salary"] += REFERRAL_REWARD

            ref_id = data.get("referred_by")
            if ref_id:
                ref_data = ensure_user(ref_id, f"User{ref_id}")
                ref_data["salary"] += REFERRAL_REWARD

            save_data(data_all)

        await query.edit_message_text(
            "🏠 *Main Menu*\n\n"
            "You successfully joined! Use the buttons below:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu()
        )
        return

    if choice == "back":
        await query.edit_message_text(
            "🏠 *Main Menu*\n\n"
            "Use buttons below to navigate:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu()
        )
        return

    if choice == "salary":
        await salary_handler.show_salary(update, context, data, username)
        return

    if choice == "refer":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        text = (
            f"👥 *Refer & Earn*\n\nInvite people using your referral link. Each person earns you +{REFERRAL_REWARD} coins.\n\n"
            f"📌 Your referral link:\n{ref_link}"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button()
        )
        return

    if choice == "withdraw":
        await salary_handler.withdraw(update, context, data)
        return

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

    if choice == "info":
        text = (
            f"ℹ️ *About SalaryBot*\n\n"
            f"• 1 referral = {REFERRAL_REWARD} coins\n"
            f"• Coins = ₹1 each\n"
            f"• Minimum withdrawal = {MIN_WITHDRAW}\n"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button()
        )
        return


def get_callback_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(button_handler)
