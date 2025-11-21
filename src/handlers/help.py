from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    keyboard = [
        [InlineKeyboardButton("📖 Основные команды", callback_data="help_commands")],
        [InlineKeyboardButton("🔧 Настройка", callback_data="help_setup")],
        [InlineKeyboardButton("⚠️ Безопасность", callback_data="help_safety")],
        [InlineKeyboardButton("⬅️ На главную", callback_data="help_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "ℹ️ Помощь по использованию бота:\n\n"
        "Выберите раздел помощи:",
        reply_markup=reply_markup
    )
