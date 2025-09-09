# inline_buttons/button_handler.py

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from data_handler import ensure_user, load_data, save_data
from inline_buttons.menu_buttons import main_menu, back_button, join_keyboard
from config import REFERRAL_REWARD, MIN_WITHDRAW, CHANNEL_USERNAME

# ---------------- JOIN CHANNEL PROMPT ----------------
async def send_join_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    """
    Sends a professional welcome message prompting the user to join the channel.
    """
    welcome_text = (
        f"👋 *Hello {username}!* \n\n"
        f"📢 Welcome to *SalaryBot* – a professional referral-based salary system.\n\n"
        f"💰 *How it works:*\n"
        f"• 1 referral = {REFERRAL_REWARD} coins (₹{REFERRAL_REWARD})\n"
        f"• Salary is calculated monthly\n"
        f"• Coins = Rupees (1 coin = ₹1)\n\n"
        f"✅ To start, please join our official channel below:"
    )
    # pass channel username explicitly to keyboard (menu_buttons should accept it)
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=join_keyboard(CHANNEL_USERNAME)
    )


# ---------------- INLINE BUTTON HANDLER ----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles all inline button clicks: main menu, join, back, salary, refer, withdraw, leaderboard, info.
    """
    query = update.callback_query
    # Always answer callback query (prevents spinner)
    await query.answer()

    user = query.from_user
    user_id = str(user.id)
    username = user.username or f"User{user.id}"

    # Ensure user exists and load the entire dataset
    ensure_user(user_id, username)
    data_all = load_data()
    data = data_all.get(user_id, {})

    choice = query.data

    # ---------------- JOIN CHANNEL ----------------
    if choice == "joined":
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)
        if member.status in ["member", "administrator", "creator"]:
            # If first time joining according to our record
            if not data.get("joined_channel", False):
                data["joined_channel"] = True

                # Reward the new user immediately
                data["coins"] = data.get("coins", 0) + REFERRAL_REWARD

                # If this user was referred, reward the referrer (only if previously marked pending)
                ref_id = data.get("referred_by")
                if ref_id:
                    ref_id_str = str(ref_id)
                    ref_data = data_all.get(ref_id_str)
                    if ref_data:
                        # If the referrer had this user in pending list, payment is due now
                        pending = ref_data.get("referrer_counted", [])
                        if user_id in pending:
                            # pay referrer
                            ref_data["coins"] = ref_data.get("coins", 0) + REFERRAL_REWARD
                            # move user to active referrals
                            ref_data.setdefault("referrals", [])
                            if user_id not in ref_data["referrals"]:
                                ref_data["referrals"].append(user_id)
                            # remove from pending list
                            pending.remove(user_id)
                            ref_data["referrer_counted"] = pending
                            # notify referrer
                            try:
                                await context.bot.send_message(
                                    chat_id=int(ref_id_str),
                                    text=(
                                        f"🎉 Good news! @{username} joined via your referral.\n"
                                        f"You earned +{REFERRAL_REWARD} coins.\n"
                                        f"💰 New balance: {ref_data.get('coins',0)} coins."
                                    )
                                )
                            except Exception:
                                # ignore send failures (user blocked bot, etc.)
                                pass

                # Notify the new user about their reward
                try:
                    await context.bot.send_message(
                        chat_id=int(user_id),
                        text=(
                            f"🎉 Welcome @{username}!\n"
                            f"You received +{REFERRAL_REWARD} coins for joining the channel.\n"
                            f"💰 Your balance: {data.get('coins',0)} coins."
                        )
                    )
                except Exception:
                    pass

                # persist changes
                data_all[user_id] = data
                save_data(data_all)

            # Show main menu after joining
            await query.edit_message_text(
                "✅ Thank you for joining the channel!\n\n🏠 *Main Menu*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu()
            )
        else:
            # still not a member
            await query.edit_message_text(
                "⚠️ You must join the channel before continuing.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=join_keyboard(CHANNEL_USERNAME)
            )
        return

    # ---------------- BACK BUTTON ----------------
    if choice == "back":
        # Use a polished main menu text (not only buttons)
        coins = data.get("coins", 0)
        refs = len(data.get("referrals", []))
        menu_text = (
            f"🟢────────────────────────🟢\n"
            f"🏠 *Main Menu*\n\n"
            f"👤 @{username}\n"
            f"💰 Balance: {coins} coins (₹{coins})\n"
            f"👥 Referrals: {refs}\n"
            f"🟢────────────────────────🟢\n"
            f"Choose an option below:"
        )
        await query.edit_message_text(menu_text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())
        return

    # ---------------- SALARY ----------------
    if choice == "salary":
        coins = data.get("coins", 0)
        refs = len(data.get("referrals", []))
        text = (
            f"💼 *My Salary Info*\n\n"
            f"👤 Username: @{username}\n"
            f"💰 Current Balance: {coins} coins (₹{coins})\n"
            f"👥 Total Referrals: {refs}\n\n"
            f"📅 Salary is calculated monthly based on active referrals.\n"
            f"💡 Keep inviting friends to increase your earnings!"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    # ---------------- REFER & EARN ----------------
    if choice == "refer":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        text = (
            f"👥 *Refer & Earn*\n\n"
            f"Each person who joins using your link and subscribes to our channel will earn *you* "
            f"+{REFERRAL_REWARD} coins and *them* +{REFERRAL_REWARD} coins.\n\n"
            f"📌 Your referral link:\n{ref_link}\n\n"
            f"🔁 Note: referral is counted once when the person actually joins the channel."
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    # ---------------- WITHDRAW ----------------
    if choice == "withdraw":
        coins = data.get("coins", 0)
        if coins < MIN_WITHDRAW:
            text = (
                f"🏦 *Withdraw Section*\n\n"
                f"⚠️ Your balance: {coins} coins.\n"
                f"You need at least {MIN_WITHDRAW} coins to withdraw.\n\n"
                f"💡 Keep referring friends to increase your monthly salary."
            )
        else:
            text = (
                f"🏦 *Withdraw Section*\n\n"
                f"✅ Eligible for withdrawal!\n"
                f"Balance: {coins} coins.\n\n"
                f"📌 Withdrawals are processed monthly. Contact admin to claim your payout."
            )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    # ---------------- LEADERBOARD ----------------
    if choice == "leaderboard":
        data_all = load_data()
        top_users = sorted(data_all.items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:10]
        text = "🏆 *Top 10 Users*\n\n"
        for i, (uid, udata) in enumerate(top_users, start=1):
            name = udata.get("name") or f"User{uid}"
            text += f"{i}. {name} — {udata.get('coins',0)} coins\n"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return

    # ---------------- INFO / HELP ----------------
    if choice == "info":
        text = (
            f"ℹ️ *About SalaryBot*\n\n"
            f"SalaryBot is a professional referral-based salary system.\n"
            f"Invite friends, earn coins, and get monthly payouts.\n\n"
            f"📌 Rules:\n"
            f"• 1 referral = {REFERRAL_REWARD} coins = ₹{REFERRAL_REWARD}\n"
            f"• Coins = Rupees (1 coin = ₹1)\n"
            f"• Minimum withdrawal = {MIN_WITHDRAW} coins\n\n"
            f"✅ Referral is counted *only once* when the invited user actually joins the channel."
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())
        return


# ---------------- CALLBACK HANDLER ----------------
def get_callback_handler() -> CallbackQueryHandler:
    """
    Returns the CallbackQueryHandler for the main bot app.
    """
    return CallbackQueryHandler(button_handler)


# ---------------- CHAT MEMBER LEAVE HANDLER ----------------
async def check_leaves(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Detects when a user leaves the channel and reduces coins from referrer.
    """
    # ChatMemberUpdated object: use old_chat_member / new_chat_member
    cm = update.chat_member
    if not cm:
        return

    old_status = cm.old_chat_member.status
    new_status = cm.new_chat_member.status
    user_obj = cm.new_chat_member.user
    user_id = str(user_obj.id)

    # Only handle real leaves (was member -> now left)
    if old_status in ["member", "administrator", "creator"] and new_status == "left":
        data_all = load_data()
        user_data = data_all.get(user_id)
        if not user_data:
            return

        # if this user was referred by someone and counted as active referral, deduct from referrer
        ref_id = user_data.get("referred_by")
        if ref_id:
            ref_id_str = str(ref_id)
            ref_data = data_all.get(ref_id_str)
            if ref_data and user_id in ref_data.get("referrals", []):
                # deduct
                ref_data["coins"] = max(0, ref_data.get("coins", 0) - REFERRAL_REWARD)
                # remove from active referrals
                ref_data["referrals"].remove(user_id)
                # notify referrer
                try:
                    await context.bot.send_message(
                        chat_id=int(ref_id_str),
                        text=(
                            f"⚠️ One of your referrals (@{user_data.get('name','User'+user_id)}) has left the channel.\n"
                            f"-{REFERRAL_REWARD} coins deducted.\n"
                            f"💰 New balance: {ref_data.get('coins',0)} coins."
                        )
                    )
                except Exception:
                    pass

        # mark this user as not joined in our records
        user_data["joined_channel"] = False
        data_all[user_id] = user_data
        save_data(data_all)
