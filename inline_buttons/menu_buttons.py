from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ---------------- CONFIG ----------------
CHANNEL_USERNAME = "@salaryget"  # Your official channel

# ---------------- BUTTONS ----------------
def main_menu():
    """
    Main menu of the bot.
    Professional, user-friendly, and descriptive options.
    Use this after the user has joined the channel.
    """
    keyboard = [
        [InlineKeyboardButton("💰 My Salary", callback_data="salary")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("🏦 Withdraw Funds", callback_data="withdraw")],
        [InlineKeyboardButton("📊 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("ℹ️ Info / Help", callback_data="info")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_button():
    """
    Simple back button.
    Takes user back to main menu from any submenu.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back")]
    ])


def join_keyboard():
    """
    Professional join prompt.
    - First button opens the channel link.
    - Second button 'Done' confirms the user has joined.
    """
    keyboard = [
        [InlineKeyboardButton("📢 Join Our Official Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("✅ I Have Joined", callback_data="joined")]
    ]
    return InlineKeyboardMarkup(keyboard)


def referral_menu():
    """
    Optional: Referral menu with instructions and copyable link.
    Could be used if you want a separate referral submenu.
    """
    keyboard = [
        [InlineKeyboardButton("📎 Copy Referral Link", callback_data="copy_referral")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)
