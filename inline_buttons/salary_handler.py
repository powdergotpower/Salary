from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from inline_buttons.menu_buttons import back_button
from config import MIN_WITHDRAW

async def show_salary(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict, username: str):
    salary = data.get("salary", 0)
    refs = len(data.get("referrer_counted", []))  # total users referred
    text = (
        f"💼 *My Salary Info*\n\n"
        f"👤 Username: @{username}\n"
        f"💰 Current Balance: {salary} coins (₹{salary})\n"
        f"👥 Total Referrals: {refs}\n\n"
        f"📅 Salary is calculated monthly based on your referrals.\n"
        f"💡 Keep inviting friends to increase your monthly earnings!"
    )
    await update.callback_query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button()
    )

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
    salary = data.get("salary", 0)
    if salary < MIN_WITHDRAW:
        text = (
            f"🏦 *Withdraw Section*\n\n"
            f"⚠️ Your balance: {salary} coins.\n"
            f"You need at least {MIN_WITHDRAW} coins to withdraw.\n"
            f"💡 Keep referring friends to increase your monthly salary!"
        )
    else:
        text = (
            f"🏦 *Withdraw Section*\n\n"
            f"✅ Eligible for withdrawal!\n"
            f"Balance: {salary} coins\n"
            f"📌 Contact admin to claim your payout."
        )
    await update.callback_query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button()
    )
