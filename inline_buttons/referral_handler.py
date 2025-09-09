from telegram import Update, User
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from data_handler import ensure_user, load_data, save_data
from inline_buttons.menu_buttons import main_menu, join_keyboard
from config import REFERRAL_REWARD, CHANNEL_LINK

async def send_join_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    welcome_text = (
        f"👋 *Hello {username}!* \n\n"
        f"📢 Welcome to *SalaryBot* – a professional referral-based salary system.\n\n"
        f"💰 *How it works:*\n"
        f"• 1 referral = {REFERRAL_REWARD} coins (₹{REFERRAL_REWARD})\n"
        f"• Salary is calculated monthly\n"
        f"• Coins = Rupees (1 coin = ₹1)\n\n"
        f"✅ To start, please join our official channel below:"
    )
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=join_keyboard()
    )

async def handle_joined(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, data: dict):
    query = update.callback_query
    member = await context.bot.get_chat_member(CHANNEL_USERNAME, user.id)

    if member.status in ["member", "administrator", "creator"]:
        data["joined_channel"] = True
        all_data = load_data()

        # Give coins to referrer + user
        if "referred_by" in data:
            ref_id = data["referred_by"]
            ref_data = ensure_user(ref_id, f"User{ref_id}")

            if "referrer_counted" not in ref_data:
                ref_data["referrer_counted"] = []

            if str(user.id) in ref_data["referrer_counted"]:
                ref_data["coins"] += REFERRAL_REWARD
                data["coins"] += REFERRAL_REWARD
                ref_data["referrer_counted"].remove(str(user.id))

                # Notify referrer
                try:
                    await context.bot.send_message(
                        chat_id=int(ref_id),
                        text=f"🎉 Your referral @{user.username or user.id} just joined!\n💰 You earned +{REFERRAL_REWARD} coins."
                    )
                except:
                    pass

        save_data(all_data)
        await query.edit_message_text(
            "✅ Thank you for joining the channel!\n\n🏠 Main Menu:",
            reply_markup=main_menu()
        )
    else:
        await query.edit_message_text(
            "⚠️ You must join the channel before continuing.",
            reply_markup=join_keyboard()
        )

async def check_leaves(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_member:
        user_id = str(update.chat_member.from_user.id)
        status = update.chat_member.new_chat_member.status

        if status == "left":
            data = load_data()
            user_data = data.get(user_id)
            if user_data and user_data.get("referred_by"):
                ref_id = user_data["referred_by"]
                ref_data = data.get(ref_id)
                if ref_data and ref_data.get("coins", 0) >= REFERRAL_REWARD:
                    ref_data["coins"] -= REFERRAL_REWARD
                    save_data(data)
