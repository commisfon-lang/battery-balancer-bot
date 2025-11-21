from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def config_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /config"""
    try:
        keyboard = [
            [InlineKeyboardButton("🔋 Тип аккумулятора", callback_data="battery_type")],
            [InlineKeyboardButton("⚡ Напряжение", callback_data="voltage")],
            [InlineKeyboardButton("🔧 Быстрая настройка", callback_data="quick_setup")],
            [InlineKeyboardButton("⬅️ На главную", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚙️ Настройка конфигурации балансировки:\n\n"
            "Выберите параметр для настройки:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Ошибка в config_handler: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке команды")

async def config_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data
        
        if data == "main_menu":
            await show_main_menu(query)
        elif data == "quick_setup":
            await show_quick_setup(query)
        elif data == "battery_type":
            await show_battery_types(query)
        elif data == "voltage":
            await show_voltage_options(query)
        elif data.startswith("battery_"):
            await handle_battery_selection(query, data)
        elif data.startswith("voltage_"):
            await handle_voltage_selection(query, data)
        elif data.startswith("quick_"):
            await handle_quick_setup(query, data)
        else:
            await query.edit_message_text("❌ Неизвестная команда")
            
    except Exception as e:
        logger.error(f"Ошибка в config_button: {e}")
        await query.edit_message_text("❌ Произошла ошибка")

async def show_main_menu(query):
    """Показать главное меню"""
    keyboard = [
        [InlineKeyboardButton("⚙️ Настроить конфигурацию", callback_data="config")],
        [InlineKeyboardButton("🔧 Быстрая настройка", callback_data="quick_setup")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔋 Battery Balancer Bot\n\nВыберите действие:",
        reply_markup=reply_markup
    )

async def show_quick_setup(query):
    """Быстрая настройка"""
    keyboard = [
        [InlineKeyboardButton("🔋 Li-ion (3.7V)", callback_data="quick_liion")],
        [InlineKeyboardButton("🔋 LiPo (3.7V)", callback_data="quick_lipo")],
        [InlineKeyboardButton("🔋 LiFePO4 (3.2V)", callback_data="quick_lifepo4")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔧 Быстрая настройка:\n\n"
        "Выберите тип аккумулятора для автоматической настройки:",
        reply_markup=reply_markup
    )

async def show_battery_types(query):
    """Показать типы аккумуляторов"""
    keyboard = [
        [InlineKeyboardButton("🔋 Li-ion", callback_data="battery_liion")],
        [InlineKeyboardButton("🔋 LiPo", callback_data="battery_lipo")],
        [InlineKeyboardButton("🔋 LiFePO4", callback_data="battery_lifepo4")],
        [InlineKeyboardButton("🔋 NiMH", callback_data="battery_nimh")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔋 Выберите тип аккумулятора:\n\n"
        "• Li-ion - литий-ионные\n"
        "• LiPo - литий-полимерные\n"
        "• LiFePO4 - литий-железо-фосфатные\n"
        "• NiMH - никель-металл-гидридные",
        reply_markup=reply_markup
    )

async def show_voltage_options(query):
    """Показать варианты напряжения"""
    keyboard = [
        [InlineKeyboardButton("⚡ 3.7V (Li-ion/LiPo)", callback_data="voltage_3.7")],
        [InlineKeyboardButton("⚡ 3.2V (LiFePO4)", callback_data="voltage_3.2")],
        [InlineKeyboardButton("⚡ 1.2V (NiMH)", callback_data="voltage_1.2")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚡ Настройка напряжения элемента:\n\n"
        "Выберите стандартное напряжение:",
        reply_markup=reply_markup
    )

async def handle_battery_selection(query, data):
    """Обработчик выбора типа аккумулятора"""
    battery_type = data.replace("battery_", "")
    type_names = {
        "liion": "Li-ion (литий-ионный)",
        "lipo": "LiPo (литий-полимерный)", 
        "lifepo4": "LiFePO4 (литий-железо-фосфатный)",
        "nimh": "NiMH (никель-металл-гидридный)"
    }
    
    battery_name = type_names.get(battery_type, battery_type)
    await query.edit_message_text(f"✅ Тип аккумулятора установлен: {battery_name}")

async def handle_voltage_selection(query, data):
    """Обработчик выбора напряжения"""
    voltage = data.replace("voltage_", "")
    await query.edit_message_text(f"✅ Напряжение элемента установлено: {voltage}V")

async def handle_quick_setup(query, data):
    """Обработчик быстрой настройки"""
    battery_type = data.replace("quick_", "")
    type_names = {
        "liion": "Li-ion",
        "lipo": "LiPo", 
        "lifepo4": "LiFePO4"
    }
    
    battery_name = type_names.get(battery_type, battery_type)
    voltage = "3.7V" if battery_type in ["liion", "lipo"] else "3.2V"
    
    await query.edit_message_text(
        f"✅ Быстрая настройка завершена!\n\n"
        f"• Тип аккумулятора: {battery_name}\n"
        f"• Напряжение элемента: {voltage}\n"
        f"• Балансировка настроена автоматически\n\n"
        f"Теперь вы можете использовать настройки для балансировки."
    )
