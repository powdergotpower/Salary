from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from data_handler import ensure_user, load_data, save_data
from inline_buttons.menu_buttons import main_menu, back_button, join_keyboard
from telegram.constants import ParseMode

REFERRAL_REWARD = 2.5
MIN_WITHDRAW = 100
CHANNEL_USERNAME = "@salaryget"

# ---------------- BUTTON HANDLER ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles all inline button clicks.
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
            save_data(data)
            await query.edit_message_text(
                "✅ Thank you for joining the channel!\n\nMain Menu:",
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
        await query.edit_message_text("🏠 Main Menu:", reply_markup=main_menu())
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
            f"📅 Salary is calculated monthly based on your referrals."
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
            f"📌 Your referral link:\n{ref_link}"
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
                f"Keep referring friends to increase your monthly salary."
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


# ---------------- LEAVES CHECK ----------------
async def check_leaves(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Detects when a referral leaves the channel and deducts coins.
    """
    if update.chat_member:
        user = update.chat_member.from_user
        status = update.chat_member.new_chat_member.status
        if status == "left":
            user_id = str(user.id)
            data = load_data()
            if user_id in data and data[user_id]["referred_by"]:
                ref_id = data[user_id]["referred_by"]
                if ref_id in data:
                    data[ref_id]["coins"] -= REFERRAL_REWARD
                    if user_id in data[ref_id]["referrals"]:
                        data[ref_id]["referrals"].remove(user_id)
                    save_data(data)
                    try:
                        await context.bot.send_message(
                            chat_id=int(ref_id),
                            text=f"⚠️ Your referral @{user.username or user_id} has left the channel.\n"
                                 f"-{REFERRAL_REWARD} coins deducted.\n"
                                 f"New balance: {data[ref_id]['coins']} coins."
                        )
                    except:
                        pass

# ---------------- CALLBACK HANDLER ----------------
def get_callback_handler():
    """
    Returns the CallbackQueryHandler for the main bot app.
    """
    return CallbackQueryHandler(button_handler)
