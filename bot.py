import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Настройка токена
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    print("📝 Создайте файл .env с содержимым:")
    print("BOT_TOKEN=ваш_токен_бота")
    exit(1)

# Упрощенная настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Глобальное хранилище данных пользователей
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    
    # Инициализация данных пользователя
    user_data[user_id] = {
        'step': 'main',
        'series': None,
        'parallel': None,
        'capacities': []
    }
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Настроить", callback_data="config")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔋 Бот для балансировки аккумуляторов 18650\n\n"
        "Нажмите 'Настроить' для начала работы:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "config":
        await show_config_menu(query, user_id)
    elif data == "help":
        await show_help(query)
    elif data == "set_series":
        user_data[user_id]['step'] = 'waiting_series'
        await query.edit_message_text("🔢 Введите количество последовательных групп (S):")
    elif data == "set_parallel":
        user_data[user_id]['step'] = 'waiting_parallel'
        await query.edit_message_text("🔢 Введите количество параллельных аккумуляторов (P):")
    elif data == "back":
        await start_callback(query)

async def show_config_menu(query, user_id):
    """Показать меню конфигурации"""
    user_config = user_data.get(user_id, {})
    
    keyboard = [
        [InlineKeyboardButton("🔢 Установить S", callback_data="set_series")],
        [InlineKeyboardButton("🔢 Установить P", callback_data="set_parallel")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    config_text = f"""⚙️ Текущая конфигурация:

🔢 S (последовательно): {user_config.get('series', 'не задано')}
🔢 P (параллельно): {user_config.get('parallel', 'не задано')}

Выберите параметр:"""
    
    await query.edit_message_text(config_text, reply_markup=reply_markup)

async def show_help(query):
    """Показать справку"""
    help_text = """ℹ️ **Помощь по боту**

Этот бот помогает сбалансировать сборку аккумуляторов 18650.

**Как использовать:**
1. Настройте конфигурацию (S и P)
2. Введите емкости аккумуляторов
3. Получите схему распайки

**Пример:**
Для 4S2P нужно 8 аккумуляторов:
2500 2550 2600 2450 2520 2480 2580 2420"""
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

async def start_callback(query):
    """Возврат в главное меню (для callback)"""
    user_id = query.from_user.id
    user_data[user_id] = {'step': 'main', 'series': None, 'parallel': None, 'capacities': []}
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Настроить", callback_data="config")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔋 Бот для балансировки аккумуляторов 18650\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    user_config = user_data.get(user_id, {})
    
    if user_config.get('step') == 'waiting_series':
        try:
            series = int(text)
            if 1 <= series <= 20:
                user_config['series'] = series
                user_config['step'] = 'main'
                await update.message.reply_text(f"✅ Установлено S = {series}")
                
                # Показываем меню конфигурации
                keyboard = [
                    [InlineKeyboardButton("🔢 Установить S", callback_data="set_series")],
                    [InlineKeyboardButton("🔢 Установить P", callback_data="set_parallel")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"⚙️ Конфигурация:\nS: {series}\nP: {user_config.get('parallel', 'не задано')}",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text("❌ Введите число от 1 до 20")
        except ValueError:
            await update.message.reply_text("❌ Введите корректное число")
    
    elif user_config.get('step') == 'waiting_parallel':
        try:
            parallel = int(text)
            if 1 <= parallel <= 20:
                user_config['parallel'] = parallel
                user_config['step'] = 'main'
                await update.message.reply_text(f"✅ Установлено P = {parallel}")
                
                # Показываем меню конфигурации
                keyboard = [
                    [InlineKeyboardButton("🔢 Установить S", callback_data="set_series")],
                    [InlineKeyboardButton("🔢 Установить P", callback_data="set_parallel")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"⚙️ Конфигурация:\nS: {user_config.get('series', 'не задано')}\nP: {parallel}",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text("❌ Введите число от 1 до 20")
        except ValueError:
            await update.message.reply_text("❌ Введите корректное число")
    
    else:
        # Если сообщение не распознано
        await update.message.reply_text(
            "Используйте кнопки меню или команду /start",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Перезапустить", callback_data="back")]
            ])
        )

def main():
    """Основная функция запуска бота"""
    try:
        print("🚀 Запуск бота...")
        print(f"🔑 Токен: {'***' + BOT_TOKEN[-4:] if BOT_TOKEN else 'НЕ НАЙДЕН'}")
        
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        
        # Запускаем бота
        print("✅ Бот успешно запущен и ожидает сообщений...")
        application.run_polling(
            drop_pending_updates=True,  # Важно для BotHost!
            allowed_updates=["message", "callback_query"]
        )
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("🔧 Возможные причины:")
        print("1. Неверный BOT_TOKEN")
        print("2. Проблемы с интернет-соединением")
        print("3. Бот заблокирован")
        print("4. Неправильные настройки BotHost")

if __name__ == "__main__":
    main()
