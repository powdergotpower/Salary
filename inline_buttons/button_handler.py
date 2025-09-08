# inline_buttons/button_handler.py

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from data_handler import ensure_user, load_data, save_data
from inline_buttons.menu_buttons import main_menu, back_button, join_keyboard
from telegram.constants import ParseMode
from config import REFERRAL_REWARD, MIN_WITHDRAW, CHANNEL_USERNAME

# ---------------- JOIN CHANNEL PROMPT ----------------
async def send_join_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    """
    Sends the professional join channel prompt when the user has not joined yet.
    """
    welcome_text = (
        f"👋 Welcome *{username}*!\n\n"
        f"📢 This is *SalaryBot*, a professional referral-based system where you earn a monthly salary.\n\n"
        f"💰 *How it works:*\n"
        f"- 1 referral = {REFERRAL_REWARD} coins (₹{REFERRAL_REWARD})\n"
        f"- Salary is calculated monthly.\n"
        f"- Coins = Rupees (1 coin = ₹1)\n\n"
        f"✅ To start, join our official channel below:"
    )
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=join_keyboard()
    )


# ---------------- BUTTON HANDLER ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles all inline buttons clicks: main menu, join, back, salary, refer, withdraw, leaderboard, info.
    """
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = str(user.id)
    username = user.username or f"User{user.id}"
    data = ensure_user(user_id, username)

    choice = query.data

    # ---------------- JOIN CHANNEL ----------------
    if choice == "joined":
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
        if member.status in ["member", "administrator", "creator"]:
            data["joined_channel"] = True
            save_data(load_data())
            await query.edit_message_text(
                "✅ Thank you for joining the channel!\n\n🏠 Main Menu:",
                reply_markup=main_menu()
            )
        else:
            await query.edit_message_text(
                "⚠️ You must join the channel before continuing.",
                reply_markup=join_keyboard()
            )
        return

    # ---------------- BACK BUTTON ----------------
    if choice == "back":
        await query.edit_message_text(
            "🏠 Main Menu:",
            reply_markup=main_menu()
        )
        return

    # ---------------- SALARY ----------------
    if choice == "salary":
        coins = data["coins"]
        refs = len(data["referrals"])
        text = (
            f"💼 *My Salary Information*\n\n"
            f"👤 Username: @{username}\n"
            f"💰 Current Balance: {coins} coins (₹{coins})\n"
            f"👥 Total Referrals: {refs}\n\n"
            f"📅 Salary is calculated monthly based on your referrals.\n"
            f"Keep inviting friends to increase your monthly earnings!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    # ---------------- REFER & EARN ----------------
    if choice == "refer":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        text = (
            f"👥 *Refer & Earn*\n\n"
            f"Invite people using your referral link. Each person who joins and subscribes to our channel "
            f"earns you +{REFERRAL_REWARD} coins.\n\n"
            f"📌 Your referral link:\n{ref_link}\n\n"
            f"💡 More referrals = higher monthly salary!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    # ---------------- WITHDRAW ----------------
    if choice == "withdraw":
        coins = data["coins"]
        if coins < MIN_WITHDRAW:
            text = (
                f"🏦 *Withdraw Section*\n\n"
                f"⚠️ Your balance: {coins} coins.\n"
                f"You need at least {MIN_WITHDRAW} coins to withdraw.\n"
                f"Keep referring friends to increase your monthly salary!"
            )
        else:
            text = (
                f"🏦 *Withdraw Section*\n\n"
                f"✅ Eligible for withdrawal!\n"
                f"Balance: {coins} coins.\n"
                f"📌 Contact admin to claim your payout."
            )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    # ---------------- LEADERBOARD ----------------
    if choice == "leaderboard":
        data_all = load_data()
        top_users = sorted(data_all.items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:10]
        text = "🏆 *Top 10 Users*\n\n"
        for i, (uid, udata) in enumerate(top_users, start=1):
            text += f"{i}. {udata.get('name','Unknown')} — {udata.get('coins',0)} coins\n"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    # ---------------- INFO / HELP ----------------
    if choice == "info":
        text = (
            f"ℹ️ *About SalaryBot*\n\n"
            f"SalaryBot is a professional referral-based salary system.\n"
            f"Invite friends, earn coins, and get monthly payouts.\n\n"
            f"📌 Rules:\n"
            f"- 1 referral = {REFERRAL_REWARD} coins = ₹{REFERRAL_REWARD}\n"
            f"- Coins = Rupees (1 coin = ₹1)\n"
            f"- Minimum withdrawal = {MIN_WITHDRAW} coins\n"
            f"- Salary is calculated monthly\n"
            f"Stay active, invite friends, and grow your earnings!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

# ---------------- CALLBACK HANDLER ----------------
def get_callback_handler():
    """
    Returns the CallbackQueryHandler for the main bot app.
    """
    return CallbackQueryHandler(button_handler)
