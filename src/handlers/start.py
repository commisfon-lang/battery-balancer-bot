from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    try:
        keyboard = [
            [InlineKeyboardButton("⚙️ Настроить конфигурацию", callback_data="config")],
            [InlineKeyboardButton("🔧 Быстрая настройка", callback_data="quick_setup")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🔋 Добро пожаловать в Battery Balancer Bot!

Этот бот поможет вам настроить параметры балансировки аккумуляторных батарей.

Основные функции:
• ⚙️ Настройка конфигурации балансировки
• 🔧 Быстрая настройка для стандартных сценариев
• 📊 Мониторинг параметров
• ℹ️ Подробная помощь

Выберите действие:
        """
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в start handler: {e}")
        await update.message.reply_text("❌ Произошла ошибка при запуске бота")
