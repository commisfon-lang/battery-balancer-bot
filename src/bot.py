import os
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# Исправляем импорты
from handlers.start import start
from handlers.config import config_handler, config_button
from handlers.help import help_handler
from utils.logger import setup_logging

def main():
    """Основная функция запуска бота"""
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Проверка токена
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден! Убедитесь, что файл .env существует и содержит токен")
        print("❌ BOT_TOKEN не найден! Создайте файл .env с содержимым: BOT_TOKEN=your_token_here")
        exit(1)
    
    try:
        # Создание приложения
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("config", config_handler))
        application.add_handler(CommandHandler("help", help_handler))
        
        # Универсальный обработчик callback'ов
        application.add_handler(CallbackQueryHandler(config_button))
        
        # Запуск бота
        logger.info("✅ Бот запускается...")
        print("✅ Бот успешно запущен! Проверьте в Telegram команду /start")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
