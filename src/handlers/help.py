from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    try:
        help_text = """
ℹ️ **Помощь по использованию бота**

**Основные команды:**
/start - Начать работу с ботом
/config - Настройка параметров балансировки  
/help - Получить помощь

**Быстрая настройка:**
Выберите тип аккумулятора для автоматической настройки всех параметров.

**Ручная настройка:**
Настройте каждый параметр отдельно для точного контроля.

**Поддерживаемые типы аккумуляторов:**
• Li-ion (3.7V)
• LiPo (3.7V) 
• LiFePO4 (3.2V)
• NiMH (1.2V)
        """
        
        await update.message.reply_text(help_text)
        
    except Exception as e:
        logger.error(f"Ошибка в help handler: {e}")
        await update.message.reply_text("❌ Произошла ошибка при показе помощи")
