from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def config_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /config"""
    keyboard = [
        [InlineKeyboardButton("🔋 Тип аккумулятора", callback_data="config_battery_type")],
        [InlineKeyboardButton("⚡ Напряжение", callback_data="config_voltage")],
        [InlineKeyboardButton("🔢 Количество элементов", callback_data="config_cell_count")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="config_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚙️ Настройка конфигурации балансировки:\n\n"
        "Выберите параметр для настройки:",
        reply_markup=reply_markup
    )

async def config_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопок конфигурации"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "config_main":
        await config_main_menu(query)
    elif query.data == "config_quick":
        await config_quick_setup(query)
    elif query.data == "config_battery_type":
        await config_battery_type(query)
    elif query.data == "config_voltage":
        await config_voltage(query)
    elif query.data == "config_back":
        await config_back(query)
    elif query.data == "help_main":
        await help_main(query)
    elif query.data.startswith("quick_"):
        await quick_setup_handler(query)
    elif query.data.startswith("battery_"):
        await battery_type_handler(query)
    elif query.data.startswith("voltage_"):
        await voltage_handler(query)

async def config_main_menu(query):
    """Главное меню конфигурации"""
    keyboard = [
        [InlineKeyboardButton("🔋 Тип аккумулятора", callback_data="config_battery_type")],
        [InlineKeyboardButton("⚡ Напряжение", callback_data="config_voltage")],
        [InlineKeyboardButton("🔢 Количество элементов", callback_data="config_cell_count")],
        [InlineKeyboardButton("⬅️ На главную", callback_data="config_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚙️ Настройка конфигурации балансировки:\n\n"
        "Выберите параметр для настройки:",
        reply_markup=reply_markup
    )

async def config_quick_setup(query):
    """Быстрая настройка"""
    keyboard = [
        [InlineKeyboardButton("🔋 Li-ion (3.7V)", callback_data="quick_liion")],
        [InlineKeyboardButton("🔋 LiPo (3.7V)", callback_data="quick_lipo")],
        [InlineKeyboardButton("🔋 LiFePO4 (3.2V)", callback_data="quick_lifepo4")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="config_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔧 Быстрая настройка:\n\n"
        "Выберите тип аккумулятора для автоматической настройки:",
        reply_markup=reply_markup
    )

async def config_battery_type(query):
    """Настройка типа аккумулятора"""
    keyboard = [
        [InlineKeyboardButton("🔋 Li-ion", callback_data="battery_liion")],
        [InlineKeyboardButton("🔋 LiPo", callback_data="battery_lipo")],
        [InlineKeyboardButton("🔋 LiFePO4", callback_data="battery_lifepo4")],
        [InlineKeyboardButton("🔋 NiMH", callback_data="battery_nimh")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="config_main")]
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

async def config_voltage(query):
    """Настройка напряжения"""
    keyboard = [
        [InlineKeyboardButton("⚡ 3.7V (Li-ion/LiPo)", callback_data="voltage_37")],
        [InlineKeyboardButton("⚡ 3.2V (LiFePO4)", callback_data="voltage_32")],
        [InlineKeyboardButton("⚡ 1.2V (NiMH)", callback_data="voltage_12")],
        [InlineKeyboardButton("🔢 Ввести вручную", callback_data="voltage_custom")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="config_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚡ Настройка напряжения элемента:\n\n"
        "Выберите стандартное напряжение или введите вручную:",
        reply_markup=reply_markup
    )

async def quick_setup_handler(query):
    """Обработчик быстрой настройки"""
    battery_type = query.data.replace("quick_", "")
    type_names = {
        "liion": "Li-ion",
        "lipo": "LiPo", 
        "lifepo4": "LiFePO4"
    }
    
    await query.edit_message_text(
        f"✅ Быстрая настройка завершена!\n\n"
        f"Тип аккумулятора: {type_names.get(battery_type, battery_type)}\n"
        f"Напряжение элемента: {'3.7V' if battery_type in ['liion', 'lipo'] else '3.2V'}\n"
        f"Балансировка настроена автоматически."
    )

async def battery_type_handler(query):
    """Обработчик выбора типа аккумулятора"""
    battery_type = query.data.replace("battery_", "")
    type_names = {
        "liion": "Li-ion (литий-ионный)",
        "lipo": "LiPo (литий-полимерный)", 
        "lifepo4": "LiFePO4 (литий-железо-фосфатный)",
        "nimh": "NiMH (никель-металл-гидридный)"
    }
    
    await query.edit_message_text(
        f"✅ Тип аккумулятора установлен: {type_names.get(battery_type, battery_type)}"
    )

async def voltage_handler(query):
    """Обработчик выбора напряжения"""
    voltage = query.data.replace("voltage_", "")
    voltage_values = {
        "37": "3.7V",
        "32": "3.2V", 
        "12": "1.2V",
        "custom": "пользовательское"
    }
    
    await query.edit_message_text(
        f"✅ Напряжение элемента установлено: {voltage_values.get(voltage, voltage)}"
    )

async def config_back(query):
    """Возврат на главную"""
    keyboard = [
        [InlineKeyboardButton("⚙️ Настроить конфигурацию", callback_data="config_main")],
        [InlineKeyboardButton("🔧 Быстрая настройка", callback_data="config_quick")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔋 Battery Balancer Bot\n\nВыберите действие:",
        reply_markup=reply_markup
    )

async def help_main(query):
    """Главное меню помощи"""
    keyboard = [
        [InlineKeyboardButton("📖 Основные команды", callback_data="help_commands")],
        [InlineKeyboardButton("🔧 Настройка", callback_data="help_setup")],
        [InlineKeyboardButton("⚠️ Безопасность", callback_data="help_safety")],
        [InlineKeyboardButton("⬅️ На главную", callback_data="config_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "ℹ️ Помощь по использованию бота:\n\n"
        "Выберите раздел помощи:",
        reply_markup=reply_markup
    )
