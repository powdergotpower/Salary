from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from data_handler import ensure_user, load_data
from inline_buttons.menu_buttons import main_menu, back_button
from inline_buttons import referral_handler, salary_handler
from config import MIN_WITHDRAW, REFERRAL_REWARD


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = str(user.id)
    username = user.username or f"User{user.id}"
    data = ensure_user(user_id, username)
    choice = query.data

    # ✅ JOINED BUTTON
    if choice == "check_joined":
        await referral_handler.handle_joined(update, context, user, data)
        return

    # ✅ BACK BUTTON
    if choice == "back":
        await query.edit_message_text(
            "🏠 *Main Menu*\n\n"
            "💰 Check your salary, referrals, leaderboard, and more using the buttons below.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu()
        )
        return

    # ✅ SALARY
    if choice == "salary":
        await salary_handler.show_salary(update, context, data, username)
        return

    # ✅ REFER
    if choice == "refer":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        text = (
            "👥 *Refer & Earn*\n\n"
            f"Invite people using your referral link. Each person who joins the channel earns you +{REFERRAL_REWARD} coins.\n\n"
            f"📌 Your referral link:\n{ref_link}\n\n"
            "💡 More referrals = higher monthly salary!"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button()
        )
        return

    # ✅ WITHDRAW
    if choice == "withdraw":
        await salary_handler.withdraw(update, context, data)
        return

    # ✅ LEADERBOARD
    if choice == "leaderboard":
        data_all = load_data()
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

    # ✅ INFO
    if choice == "info":
        text = (
            "ℹ️ *About SalaryBot*\n\n"
            "SalaryBot is a professional referral-based salary system.\n"
            "Invite friends, earn coins, and get monthly payouts.\n\n"
            "📌 Rules:\n"
            f"• 1 referral = {REFERRAL_REWARD} coins = ₹{REFERRAL_REWARD}\n"
            "• Coins = Rupees (1 coin = ₹1)\n"
            f"• Minimum withdrawal = {MIN_WITHDRAW} coins\n"
            "• Salary is calculated monthly\n\n"
            "💡 Stay active, invite friends, and grow your earnings!"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button()
        )
        return


def get_callback_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(button_handler)
