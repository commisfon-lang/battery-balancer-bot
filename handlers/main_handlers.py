from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("⚙️ Настроить конфигурацию", callback_data="config")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔋 Добро пожаловать в бот для балансировки аккумуляторов!",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на inline-кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "config":
        await query.edit_message_text("⚙️ Настройка конфигурации...")
    elif query.data == "help":
        await query.edit_message_text("ℹ️ Помощь по использованию бота...")