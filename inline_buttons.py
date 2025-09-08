from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from data_handler import load_data, save_data

REFERRAL_REWARD = 2.5
MIN_WITHDRAW = 100

def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 My Salary", callback_data="salary")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("🏦 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📊 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("ℹ️ Info / Help", callback_data="info")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])

async def handle_buttons(update, context):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = str(user.id)
    username = user.username or f"User{user.id}"

    data = load_data()
    if user_id not in data:
        await query.edit_message_text("⚠️ User data not found. Please use /start.")
        return
    user_data = data[user_id]

    choice = query.data

    # ---------------- BUTTON LOGIC ----------------
    if choice == "back":
        await query.edit_message_text("🏠 Main Menu:", reply_markup=main_menu())
        return

    elif choice == "salary":
        coins = user_data["coins"]
        refs = len(user_data["referrals"])
        text = (
            f"💼 *My Salary Information*\n\n"
            f"👤 Username: @{username}\n"
            f"💰 Current Balance: {coins} coins (₹{coins})\n"
            f"👥 Total Referrals: {refs}\n\n"
            f"📅 Your salary is calculated monthly based on referrals.\n"
            f"💡 Keep referring friends to increase your earnings!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    elif choice == "refer":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        text = (
            f"👥 *Refer & Earn*\n\n"
            f"Invite friends using your referral link. Each person who joins and subscribes to our channel "
            f"earns you +{REFERRAL_REWARD} coins and them +{REFERRAL_REWARD} coins!\n\n"
            f"📌 Your referral link:\n{ref_link}\n\n"
            f"💡 More referrals = bigger monthly salary!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    elif choice == "withdraw":
        coins = user_data["coins"]
        if coins < MIN_WITHDRAW:
            text = (
                f"🏦 *Withdraw Section*\n\n"
                f"⚠️ Your balance: {coins} coins.\n"
                f"Minimum coins to withdraw: {MIN_WITHDRAW}\n\n"
                f"💡 Refer more friends to increase your salary."
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

    elif choice == "leaderboard":
        all_data = load_data()
        top_users = sorted(all_data.items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:10]
        text = "🏆 *Top 10 Users*\n\n"
        for i, (uid, udata) in enumerate(top_users, start=1):
            text += f"{i}. {udata.get('name','Unknown')} — {udata.get('coins',0)} coins\n"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    elif choice == "info":
        text = (
            f"ℹ️ *About SalaryBot*\n\n"
            f"SalaryBot is a professional referral-based salary system.\n"
            f"Earn monthly coins by inviting friends to our channel.\n\n"
            f"📌 Rules:\n"
            f"- 1 referral = {REFERRAL_REWARD} coins (₹{REFERRAL_REWARD})\n"
            f"- Coins = Rupees (1 coin = ₹1)\n"
            f"- Minimum withdrawal = {MIN_WITHDRAW} coins\n"
            f"- Salary calculated monthly\n\n"
            f"💡 Keep active, invite friends, and grow your earnings!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return
