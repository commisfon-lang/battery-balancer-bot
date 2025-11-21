import os
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from handlers.start import start
from handlers.config import config_handler, config_button
from handlers.help import help_handler
from utils.logger import setup_logging

def main():
    """Основная функция запуска бота"""
    # Настройка логирования
    setup_logging()
    
    # Проверка токена
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logging.error("❌ BOT_TOKEN не найден! Убедитесь, что файл .env существует и содержит токен")
        exit(1)
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("config", config_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CallbackQueryHandler(config_button, pattern="^config_"))
    application.add_handler(CallbackQueryHandler(config_button, pattern="^help_"))
    application.add_handler(CallbackQueryHandler(config_button, pattern="^quick_"))
    application.add_handler(CallbackQueryHandler(config_button, pattern="^battery_"))
    application.add_handler(CallbackQueryHandler(config_button, pattern="^voltage_"))
    
    # Запуск бота
    logging.info("✅ Бот запускается...")
    application.run_polling()

if __name__ == "__main__":
    main()
