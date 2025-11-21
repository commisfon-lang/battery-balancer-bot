from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from handlers import start, button_handler

class Bot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков команд и callback'ов"""
        self.application.add_handler(CommandHandler("start", start))
        self.application.add_handler(CallbackQueryHandler(button_handler))
    
    def run(self):
        """Запуск бота"""
        self.application.run_polling()