from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import CHANNEL_USERNAME

def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 My Salary", callback_data="salary")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("🏦 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back")]]
    return InlineKeyboardMarkup(keyboard)

def join_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton("✅ I Joined", callback_data="joined")],
    ]
    return InlineKeyboardMarkup(keyboard)
