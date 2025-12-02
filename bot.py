import logging
import csv
import io
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from typing import List, Dict, Tuple

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создайте обработчик для файла
file_handler = logging.FileHandler('battery_bot.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class BatteryBalancer:
    def __init__(self):
        self.user_data = {}
    
    def validate_capacities(self, capacities: List[int]) -> Tuple[bool, str]:
        """Проверка корректности емкостей"""
        if not capacities or len(capacities) == 0:
            return False, "Не введено ни одной емкости"
        
        if any(cap <= 0 for cap in capacities):
            return False, "Емкости должны быть положительными числами"
        
        if any(cap < 500 for cap in capacities):
            return False, "Емкости менее 500 мАч не реалистичны для 18650"
        
        if any(cap > 10000 for cap in capacities):
            return False, "Емкости более 10000 мАч не реалистичны для 18650"
        
        min_cap = min(capacities)
        max_cap = max(capacities)
        if max_cap / min_cap > 10:
            return False, "Слишком большой разброс емкостей (более 10 раз)"
        
        return True, "OK"
    
    def validate_configuration(self, series: int, parallel: int) -> Tuple[bool, str]:
        """Проверка корректности конфигурации"""
        if series is None or parallel is None:
            return False, "Не задана конфигурация S и P"
        
        if not (1 <= series <= 50):
            return False, "Количество последовательных групп (S) должно быть от 1 до 50"
        
        if not (1 <= parallel <= 50):
            return False, "Количество параллельных аккумуляторов (P) должно быть от 1 до 50"
        
        total_cells = series * parallel
        if total_cells > 200:
            return False, "Слишком большая сборка (максимум 200 аккумуляторов)"
        
        return True, "OK"
    
    def validate_voltage(self, voltage: float) -> Tuple[bool, str]:
        """Проверка корректности напряжения"""
        if not (2.5 <= voltage <= 4.5):
            return False, "Напряжение должно быть в диапазоне 2.5-4.5 В"
        
        return True, "OK"

    def balance_batteries_repackr(self, capacities: List[int], series: int, parallel: int) -> List[Dict]:
        """Улучшенный алгоритм балансировки по принципу repackr"""
        try:
            # Проверка на None значения
            if capacities is None or series is None or parallel is None:
                raise ValueError("Не все параметры заданы")
            
            # Валидация входных данных
            is_valid, error_msg = self.validate_capacities(capacities)
            if not is_valid:
                raise ValueError(f"Неверные данные емкостей: {error_msg}")
            
            is_valid, error_msg = self.validate_configuration(series, parallel)
            if not is_valid:
                raise ValueError(f"Неверная конфигурация: {error_msg}")
            
            total_cells = len(capacities)
            cells_per_group = parallel
            
            if total_cells != series * parallel:
                raise ValueError(f"Количество аккумуляторов ({total_cells}) не соответствует конфигурации {series}S{parallel}P")
            
            # Создаем массив объектов с емкостями
            cells = [{'capacity': cap, 'index': i} for i, cap in enumerate(capacities)]
            
            # Сортируем по убыванию емкости
            cells.sort(key=lambda x: x['capacity'], reverse=True)
            
            # Рассчитываем целевую емкость
            total_capacity = sum(cell['capacity'] for cell in cells)
            target_capacity = total_capacity / series
            
            best_solution = None
            best_score = float('inf')
            
            # Пробуем несколько стратегий
            for attempt in range(3):
                test_groups = [{'cells': [], 'capacity': 0} for _ in range(series)]
                available_cells = cells.copy()
                
                if attempt == 0:
                    # Стратегия 1: Равномерное распределение
                    for i, cell in enumerate(available_cells):
                        group_idx = i % series
                        if len(test_groups[group_idx]['cells']) < cells_per_group:
                            test_groups[group_idx]['cells'].append(cell)
                            test_groups[group_idx]['capacity'] += cell['capacity']
                elif attempt == 1:
                    # Стратегия 2: Жадный алгоритм
                    available_cells.sort(key=lambda x: x['capacity'], reverse=True)
                    for cell in available_cells:
                        best_group_idx = -1
                        best_diff = float('inf')
                        
                        for j, group in enumerate(test_groups):
                            if len(group['cells']) < cells_per_group:
                                new_capacity = group['capacity'] + cell['capacity']
                                diff = abs(new_capacity - target_capacity)
                                if diff < best_diff:
                                    best_diff = diff
                                    best_group_idx = j
                        
                        if best_group_idx != -1:
                            test_groups[best_group_idx]['cells'].append(cell)
                            test_groups[best_group_idx]['capacity'] += cell['capacity']
                else:
                    # Стратегия 3: Парное распределение
                    available_cells.sort(key=lambda x: x['capacity'], reverse=True)
                    mid_point = len(available_cells) // 2
                    large_cells = available_cells[:mid_point]
                    small_cells = available_cells[mid_point:]
                    
                    # Распределяем большие аккумуляторы
                    for i, cell in enumerate(large_cells):
                        group_idx = i % series
                        if len(test_groups[group_idx]['cells']) < cells_per_group:
                            test_groups[group_idx]['cells'].append(cell)
                            test_groups[group_idx]['capacity'] += cell['capacity']
                    
                    # Распределяем маленькие в обратном порядке
                    for i, cell in enumerate(small_cells):
                        group_idx = (series - 1 - (i % series))
                        if len(test_groups[group_idx]['cells']) < cells_per_group:
                            test_groups[group_idx]['cells'].append(cell)
                            test_groups[group_idx]['capacity'] += cell['capacity']
                
                # Оптимизация перестановками
                for optimization_round in range(10):
                    improved = False
                    for i in range(series):
                        for j in range(i + 1, series):
                            for k in range(len(test_groups[i]['cells'])):
                                for l in range(len(test_groups[j]['cells'])):
                                    cell_a = test_groups[i]['cells'][k]
                                    cell_b = test_groups[j]['cells'][l]
                                    
                                    current_dev = (abs(test_groups[i]['capacity'] - target_capacity) + 
                                                 abs(test_groups[j]['capacity'] - target_capacity))
                                    
                                    new_cap_i = test_groups[i]['capacity'] - cell_a['capacity'] + cell_b['capacity']
                                    new_cap_j = test_groups[j]['capacity'] - cell_b['capacity'] + cell_a['capacity']
                                    new_dev = abs(new_cap_i - target_capacity) + abs(new_cap_j - target_capacity)
                                    
                                    if new_dev < current_dev:
                                        test_groups[i]['cells'][k] = cell_b
                                        test_groups[j]['cells'][l] = cell_a
                                        test_groups[i]['capacity'] = new_cap_i
                                        test_groups[j]['capacity'] = new_cap_j
                                        improved = True
                    
                    if not improved:
                        break
                
                # Оценка качества
                max_deviation = max(abs(group['capacity'] - target_capacity) for group in test_groups)
                avg_deviation = sum(abs(group['capacity'] - target_capacity) for group in test_groups) / series
                score = max_deviation * 0.6 + avg_deviation * 0.4
                
                if score < best_score:
                    best_score = score
                    best_solution = [group.copy() for group in test_groups]
            
            logger.info(f"Балансировка завершена: {series}S{parallel}P, {len(capacities)} аккумуляторов")
            return best_solution or test_groups
            
        except Exception as e:
            logger.error(f"Ошибка в balance_batteries_repackr: {e}")
            raise

    def calculate_statistics(self, groups: List[Dict], series: int, voltage: float) -> Dict:
        """Расчет статистики сборки"""
        total_capacity = sum(group['capacity'] for group in groups) / series
        total_voltage = voltage * series
        total_energy = (total_capacity * total_voltage) / 1000
        total_cells = sum(len(group['cells']) for group in groups)
        
        # Статистика отклонений
        group_capacities = [group['capacity'] for group in groups]
        deviations = [abs(cap - total_capacity) for cap in group_capacities]
        max_deviation = max(deviations)
        avg_deviation = sum(deviations) / len(deviations)
        
        # Качество балансировки
        balance_score = max(0, 100 - (max_deviation / total_capacity * 100)) if total_capacity > 0 else 0
        
        return {
            'total_capacity': total_capacity,
            'total_voltage': total_voltage,
            'total_energy': total_energy,
            'total_cells': total_cells,
            'avg_capacity': total_capacity,
            'max_deviation': max_deviation,
            'avg_deviation': avg_deviation,
            'balance_quality': balance_score,
            'group_capacities': group_capacities
        }

    def create_wiring_diagram(self, groups: List[Dict], stats: Dict) -> str:
        """Создание текстовой схемы распайки"""
        diagram = "🔋 СХЕМА РАСПАЙКИ 🔋\n\n"
        
        for i, group in enumerate(groups, 1):
            deviation = group['capacity'] - stats['avg_capacity']
            deviation_percent = (deviation / stats['avg_capacity'] * 100) if stats['avg_capacity'] > 0 else 0
            abs_deviation = abs(deviation)
            
            # Статус балансировки
            if abs_deviation <= 5:
                status = "💚 Идеально"
            elif abs_deviation <= 20:
                status = "💙 Хорошо"
            elif abs_deviation <= 50:
                status = "💛 Средне"
            else:
                status = "❤️ Плохо"
            
            diagram += f"🏷️ Группа {i}:\n"
            capacities_str = ' + '.join(str(cell['capacity']) for cell in group['cells'])
            diagram += f"🔋 Аккумуляторы: {capacities_str}\n"
            diagram += f"📊 Суммарно: {group['capacity']:.0f} мАч\n"
            diagram += f"⚖️ Отклонение: {deviation:+.0f} мАч ({deviation_percent:+.1f}%)\n"
            diagram += f"📈 {status}\n\n"
        
        return diagram

    def create_csv_file(self, groups: List[Dict], stats: Dict, series: int, parallel: int, voltage: float) -> io.BytesIO:
        """Создание CSV файла с результатами и обработкой исключений"""
        try:
            output = io.StringIO()
            writer = csv.writer(output, delimiter=';')
            
            # Основная информация
            writer.writerow(["Конфигурация сборки аккумуляторов 18650"])
            writer.writerow([])
            writer.writerow(["Параметр", "Значение"])
            writer.writerow(["Конфигурация", f"{series}S{parallel}P"])
            writer.writerow(["Общая емкость", f"{stats['total_capacity']:.0f} мАч"])
            writer.writerow(["Напряжение", f"{stats['total_voltage']:.2f} В"])
            writer.writerow(["Энергия", f"{stats['total_energy']:.2f} Вт·ч"])
            writer.writerow(["Количество аккумуляторов", f"{stats['total_cells']} шт"])
            writer.writerow(["Средняя емкость группы", f"{stats['avg_capacity']:.0f} мАч"])
            writer.writerow([])
            
            # Статистика
            writer.writerow(["Статистика балансировки"])
            writer.writerow(["Параметр", "Значение"])
            writer.writerow(["Максимальное отклонение", f"{stats['max_deviation']:.0f} мАч"])
            writer.writerow(["Среднее отклонение", f"{stats['avg_deviation']:.0f} мАч"])
            writer.writerow(["Качество балансировки", f"{stats['balance_quality']:.1f} %"])
            writer.writerow([])
            
            # Схема распайки
            writer.writerow(["Схема распайки"])
            writer.writerow(["Группа", "Аккумуляторы (мАч)", "Суммарная емкость (мАч)", "Отклонение (мАч)", "Отклонение (%)", "Статус"])
            
            for i, group in enumerate(groups, 1):
                batteries = '+'.join(str(cell['capacity']) for cell in group['cells'])
                deviation = group['capacity'] - stats['avg_capacity']
                deviation_percent = (deviation / stats['avg_capacity'] * 100) if stats['avg_capacity'] > 0 else 0
                abs_deviation = abs(deviation)
                
                status = "Идеально"
                if abs_deviation > 50: status = "Плохо"
                elif abs_deviation > 20: status = "Средне"
                elif abs_deviation > 5: status = "Хорошо"
                
                writer.writerow([
                    f"Группа {i}",
                    batteries,
                    f"{group['capacity']:.0f}",
                    f"{deviation:+.0f}",
                    f"{deviation_percent:+.1f}%",
                    status
                ])
            
            # Конвертируем в bytes
            csv_bytes = io.BytesIO()
            csv_bytes.write(output.getvalue().encode('utf-8-sig'))
            csv_bytes.seek(0)
            return csv_bytes
            
        except Exception as e:
            logger.error(f"CSV creation error: {e}")
            # Возвращаем файл с сообщением об ошибке
            error_content = f"Ошибка при создании CSV файла: {str(e)}"
            csv_bytes = io.BytesIO()
            csv_bytes.write(error_content.encode('utf-8'))
            csv_bytes.seek(0)
            return csv_bytes

# Создаем экземпляр балансировщика
balancer = BatteryBalancer()

def get_help_text() -> str:
    """Получить текст помощи"""
    return """ℹ️ ПОМОЩЬ ПО ИСПОЛЬЗОВАНИЮ БОТА

🔋 Этот бот помогает создать сбалансированную сборку аккумуляторов 18650.

📋 КАК ПОЛЬЗОВАТЬСЯ:
1. ⚙️ Настройте конфигурацию (S и P)
2. 📝 Введите емкости всех аккумуляторов
3. 📊 Рассчитайте оптимальное распределение
4. 💾 Скачайте результаты в CSV

🔧 КОМАНДЫ:
/start - начать работу
/reset - сбросить все данные
/status - показать текущее состояние
/cancel - отменить текущую операцию
/help - показать эту справку

📖 ОБОЗНАЧЕНИЯ:
• 🔢 S - количество последовательных групп
• 🔢 P - количество параллельных аккумуляторов в группе
• 🔋 мАч - емкость аккумулятора
• ⚖️ Отклонение - разница от средней емкости группы

💡 ПРИМЕР:
Для сборки 4S2P нужно 8 аккумуляторов.
Введите их емкости, например: 2500 2550 2600 2450 2520 2480 2580 2420

⚠️ ОГРАНИЧЕНИЯ:
• Максимум 200 аккумуляторов в сборке
• Емкости: 500-10000 мАч
• Напряжение: 2.5-4.5 В"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    
    # Инициализируем данные пользователя
    balancer.user_data[user_id] = {
        'step': 'config',
        'series': None,
        'parallel': None,
        'voltage': 3.7,
        'capacities': []
    }
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Настроить конфигурацию", callback_data="config")],
        [InlineKeyboardButton("📊 Рассчитать сборку", callback_data="calculate")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔋 Добро пожаловать в бот для балансировки аккумуляторов 18650!\n\n"
        "Я помогу вам оптимально распределить аккумуляторы по параллельным группам "
        "для создания сбалансированной сборки.\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /reset - сброс данных пользователя"""
    user_id = update.effective_user.id
    
    if user_id in balancer.user_data:
        del balancer.user_data[user_id]
    
    # Инициализируем заново
    balancer.user_data[user_id] = {
        'step': 'config',
        'series': None,
        'parallel': None,
        'voltage': 3.7,
        'capacities': []
    }
    
    await update.message.reply_text(
        "✅ Все данные сброшены! Начинаем заново.\n\n"
        "Используйте /start для начала работы или настройте конфигурацию:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Настроить конфигурацию", callback_data="config")]
        ])
    )

async def show_progress(message, progress: int, total: int = 100):
    """Показать прогресс-бар"""
    bars = "█" * (progress // 10)
    spaces = " " * (10 - (progress // 10))
    
    try:
        await message.edit_text(
            f"🔄 Выполняется расчет оптимальной балансировки...\n\n"
            f"📊 Прогресс: [{bars}{spaces}] {progress}%\n"
            f"⏳ Пожалуйста, подождите..."
        )
    except Exception as e:
        logger.debug(f"Progress update failed: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Обработка неожиданных состояний - инициализация данных пользователя если их нет
    if user_id not in balancer.user_data:
        balancer.user_data[user_id] = {
            'step': 'config',
            'series': None,
            'parallel': None,
            'voltage': 3.7,
            'capacities': []
        }
    
    data = query.data
    
    if data == "config":
        await config_handler(query, context)
    elif data == "calculate":
        await calculate_handler(query, context)
    elif data == "help":
        await help_handler(query, context)
    elif data == "back":
        await start_callback(query, context)
    elif data == "set_series":
        await set_series_handler(query, context)
    elif data == "set_parallel":
        await set_parallel_handler(query, context)
    elif data == "set_voltage":
        await set_voltage_handler(query, context)
    elif data == "set_capacities":
        await set_capacities_handler(query, context)
    elif data == "download_csv":
        await download_csv_handler(query, context)

async def config_handler(query, context):
    """Настройка конфигурации"""
    user_id = query.from_user.id
    
    # Обработка неожиданных состояний
    if user_id not in balancer.user_data:
        await start_callback(query, context)
        return
        
    user_data = balancer.user_data.get(user_id, {})
    
    keyboard = [
        [InlineKeyboardButton("🔢 Количество последовательно (S)", callback_data="set_series")],
        [InlineKeyboardButton("🔢 Количество параллельно (P)", callback_data="set_parallel")],
        [InlineKeyboardButton("⚡ Напряжение аккумулятора", callback_data="set_voltage")],
        [InlineKeyboardButton("📝 Ввести емкости", callback_data="set_capacities")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    config_text = f"""⚙️ Текущая конфигурация:

🔢 Последовательно (S): {user_data.get('series', 'не задано')}
🔢 Параллельно (P): {user_data.get('parallel', 'не задано')}
⚡ Напряжение: {user_data.get('voltage', 3.7)} В
📊 Аккумуляторов: {len(user_data.get('capacities', []))} шт

Выберите параметр для настройки:"""
    
    await query.edit_message_text(config_text, reply_markup=reply_markup)

async def set_series_handler(query, context):
    """Установка количества последовательных групп"""
    user_id = query.from_user.id
    
    # Обработка неожиданных состояний
    if user_id not in balancer.user_data:
        await start_callback(query, context)
        return
        
    user_data = balancer.user_data.get(user_id, {})
    user_data['step'] = 'waiting_series'
    
    await query.edit_message_text(
        "🔢 Введите количество последовательных групп (S) от 1 до 50:\n\n"
        "Пример: 4\n\n"
        "💡 Для отмены используйте /reset"
    )

async def set_parallel_handler(query, context):
    """Установка количества параллельных аккумуляторов"""
    user_id = query.from_user.id
    
    # Обработка неожиданных состояний
    if user_id not in balancer.user_data:
        await start_callback(query, context)
        return
        
    user_data = balancer.user_data.get(user_id, {})
    user_data['step'] = 'waiting_parallel'
    
    await query.edit_message_text(
        "🔢 Введите количество параллельных аккумуляторов (P) от 1 до 50:\n\n"
        "Пример: 2\n\n"
        "💡 Для отмены используйте /reset"
    )

async def set_voltage_handler(query, context):
    """Установка напряжения аккумулятора"""
    user_id = query.from_user.id
    
    # Обработка неожиданных состояний
    if user_id not in balancer.user_data:
        await start_callback(query, context)
        return
        
    user_data = balancer.user_data.get(user_id, {})
    user_data['step'] = 'waiting_voltage'
    
    await query.edit_message_text(
        "⚡ Введите напряжение одного аккумулятора (2.5-4.5 В):\n\n"
        "Пример: 3.7\n\n"
        "💡 Обычно используется 3.6-3.7 В\n"
        "💡 Для отмены используйте /reset"
    )

async def set_capacities_handler(query, context):
    """Ввод емкостей аккумуляторов"""
    user_id = query.from_user.id
    
    # Обработка неожиданных состояний
    if user_id not in balancer.user_data:
        await start_callback(query, context)
        return
        
    user_data = balancer.user_data.get(user_id, {})
    
    series = user_data.get('series')
    parallel = user_data.get('parallel')
    
    if not series or not parallel:
        await query.edit_message_text(
            "❌ Сначала настройте конфигурацию (S и P)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Настроить", callback_data="config")]])
        )
        return
    
    required_cells = series * parallel
    user_data['step'] = 'waiting_capacities'
    
    await query.edit_message_text(
        f"📝 Введите емкости {required_cells} аккумуляторов через пробел:\n\n"
        f"Пример для {required_cells} аккумуляторов:\n"
        f"2500 2550 2600 2450 2520 2480 2580 2420\n\n"
        f"Диапазон: 500-10000 мАч\n"
        f"Разделитель: пробел\n\n"
        f"💡 Для отмены используйте /reset"
    )

async def calculate_handler(query, context):
    """Расчет сборки с прогресс-баром"""
    user_id = query.from_user.id
    
    # Проверяем наличие данных пользователя
    if user_id not in balancer.user_data:
        await query.edit_message_text(
            "❌ Данные не найдены. Начните с команды /start",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Начать заново", callback_data="back")]])
        )
        return
    
    user_data = balancer.user_data[user_id]
    
    # Проверяем наличие всех необходимых данных
    if user_data is None or not user_data.get('series') or not user_data.get('parallel'):
        await query.edit_message_text(
            "❌ Сначала настройте конфигурацию (S и P)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Настроить", callback_data="config")]])
        )
        return
    
    capacities = user_data.get('capacities', [])
    required_cells = user_data['series'] * user_data['parallel']
    
    if len(capacities) != required_cells:
        await query.edit_message_text(
            f"❌ Необходимо ввести емкости для {required_cells} аккумуляторов\n"
            f"Сейчас введено: {len(capacities)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Ввести емкости", callback_data="set_capacities")]])
        )
        return
    
    # Начинаем расчет с прогресс-баром
    progress_msg = await query.edit_message_text("🔄 Выполняется расчет оптимальной балансировки...\n\n📊 Прогресс: [          ] 0%")
    
    try:
        series = user_data['series']
        parallel = user_data['parallel']
        voltage = user_data.get('voltage', 3.7)
        
        # Обновляем прогресс
        await show_progress(progress_msg, 10)
        await asyncio.sleep(0.5)
        
        # Валидация данных перед расчетом
        is_valid, error_msg = balancer.validate_configuration(series, parallel)
        if not is_valid:
            await progress_msg.edit_text(f"❌ Ошибка конфигурации: {error_msg}")
            return
            
        is_valid, error_msg = balancer.validate_capacities(capacities)
        if not is_valid:
            await progress_msg.edit_text(f"❌ Ошибка в данных емкостей: {error_msg}")
            return
            
        is_valid, error_msg = balancer.validate_voltage(voltage)
        if not is_valid:
            await progress_msg.edit_text(f"❌ Ошибка в напряжении: {error_msg}")
            return
        
        # Обновляем прогресс
        await show_progress(progress_msg, 30)
        await asyncio.sleep(0.5)
        
        # Балансируем аккумуляторы
        await show_progress(progress_msg, 50)
        groups = balancer.balance_batteries_repackr(capacities, series, parallel)
        
        # Обновляем прогресс
        await show_progress(progress_msg, 80)
        await asyncio.sleep(0.5)
        
        # Рассчитываем статистику
        stats = balancer.calculate_statistics(groups, series, voltage)
        
        # Создаем схему распайки
        diagram = balancer.create_wiring_diagram(groups, stats)
        
        # Создаем CSV файл
        csv_file = balancer.create_csv_file(groups, stats, series, parallel, voltage)
        
        # Завершаем прогресс
        await show_progress(progress_msg, 100)
        await asyncio.sleep(0.5)
        
        # Формируем сообщение с результатами
        result_text = f"""✅ РАСЧЕТ ЗАВЕРШЕН

📊 ОБЩАЯ ИНФОРМАЦИЯ:
🔋 Конфигурация: {series}S{parallel}P
⚡ Напряжение: {stats['total_voltage']:.1f} В
🔋 Емкость: {stats['total_capacity']:.0f} мАч
⚡ Энергия: {stats['total_energy']:.2f} Вт·ч
🔢 Аккумуляторов: {stats['total_cells']} шт

📈 СТАТИСТИКА БАЛАНСИРОВКИ:
📊 Средняя емкость группы: {stats['avg_capacity']:.0f} мАч
⚖️ Максимальное отклонение: {stats['max_deviation']:.0f} мАч
📊 Среднее отклонение: {stats['avg_deviation']:.0f} мАч
✅ Качество балансировки: {stats['balance_quality']:.1f}%

{diagram}"""

        keyboard = [
            [InlineKeyboardButton("💾 Скачать CSV", callback_data="download_csv")],
            [InlineKeyboardButton("🔄 Новый расчет", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Сохраняем результаты для скачивания
        context.user_data['last_csv'] = csv_file
        context.user_data['last_filename'] = f"battery_config_{series}S{parallel}P.csv"
        
        await progress_msg.edit_text(result_text, reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Calculation error: {e}")
        error_text = f"❌ Произошла ошибка при расчете: {str(e)}\n\nПожалуйста, проверьте введенные данные и попробуйте снова."
        await progress_msg.edit_text(
            error_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="config")]])
        )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отмена текущей операции"""
    user_id = update.effective_user.id
    
    if user_id in balancer.user_data:
        balancer.user_data[user_id]['step'] = 'config'
    
    await update.message.reply_text(
        "✅ Текущая операция отменена. Вы возвращены в главное меню.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="back")]])
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать текущее состояние"""
    user_id = update.effective_user.id
    
    if user_id not in balancer.user_data:
        await update.message.reply_text("❌ Нет активной сессии. Используйте /start")
        return
    
    user_data = balancer.user_data[user_id]
    
    status_text = f"""📋 ТЕКУЩЕЕ СОСТОЯНИЕ:

🔢 Последовательно (S): {user_data.get('series', 'не задано')}
🔢 Параллельно (P): {user_data.get('parallel', 'не задано')}
⚡ Напряжение: {user_data.get('voltage', 3.7)} В
📊 Введено аккумуляторов: {len(user_data.get('capacities', []))} шт
📈 Требуется аккумуляторов: {user_data.get('series', 0) * user_data.get('parallel', 0) if user_data.get('series') and user_data.get('parallel') else 'не задано'} шт"""

    await update.message.reply_text(status_text)

async def help_handler(query, context):
    """Помощь"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(get_help_text(), reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_help_text(), reply_markup=reply_markup)

async def download_csv_handler(query, context):
    """Скачивание CSV файла"""
    csv_file = context.user_data.get('last_csv')
    filename = context.user_data.get('last_filename', 'battery_config.csv')
    
    if csv_file:
        try:
            await query.message.reply_document(
                document=csv_file,
                filename=filename,
                caption="📁 Файл с результатами балансировки"
            )
            await query.answer("✅ Файл отправлен")
        except Exception as e:
            logger.error(f"File send error: {e}")
            await query.answer("❌ Ошибка отправки файла", show_alert=True)
    else:
        await query.answer("❌ Файл не найден", show_alert=True)

async def start_callback(query, context):
    """Возврат в главное меню"""
    user_id = query.from_user.id
    
    # Сбрасываем данные пользователя
    balancer.user_data[user_id] = {
        'step': 'config',
        'series': None,
        'parallel': None,
        'voltage': 3.7,
        'capacities': []
    }
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Настроить конфигурацию", callback_data="config")],
        [InlineKeyboardButton("📊 Рассчитать сборку", callback_data="calculate")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔋 Добро пожаловать в бот для балансировки аккумуляторов 18650!\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений с улучшенной валидацией"""
    user_id = update.effective_user.id
    text = update.message.text.strip().lower()
    
    # Обработка команд
    if text == '/cancel':
        await cancel_command(update, context)
        return
    
    if text == '/reset':
        await reset_command(update, context)
        return
    
    if text == '/status':
        await status_command(update, context)
        return
    
    if text == '/help':
        await help_command(update, context)
        return
    
    # Обработка неожиданных состояний - инициализация если данных нет
    if user_id not in balancer.user_data:
        balancer.user_data[user_id] = {
            'step': 'config',
            'series': None,
            'parallel': None,
            'voltage': 3.7,
            'capacities': []
        }
    
    user_data = balancer.user_data[user_id]
    
    if user_data.get('step') == 'waiting_series':
        try:
            series = int(text)
            is_valid, error_msg = balancer.validate_configuration(series, 1)  # Проверяем только series
            if is_valid:
                user_data['series'] = series
                user_data['step'] = 'config'
                await update.message.reply_text(f"✅ Установлено последовательно: {series}S")
                await show_config_menu(update, context)
            else:
                await update.message.reply_text(f"❌ {error_msg}")
        except ValueError:
            await update.message.reply_text("❌ Введите корректное целое число")
    
    elif user_data.get('step') == 'waiting_parallel':
        try:
            parallel = int(text)
            is_valid, error_msg = balancer.validate_configuration(1, parallel)  # Проверяем только parallel
            if is_valid:
                user_data['parallel'] = parallel
                user_data['step'] = 'config'
                await update.message.reply_text(f"✅ Установлено параллельно: {parallel}P")
                await show_config_menu(update, context)
            else:
                await update.message.reply_text(f"❌ {error_msg}")
        except ValueError:
            await update.message.reply_text("❌ Введите корректное целое число")
    
    elif user_data.get('step') == 'waiting_voltage':
        try:
            voltage = float(text.replace(',', '.'))  # Поддержка запятых как разделителей
            is_valid, error_msg = balancer.validate_voltage(voltage)
            if is_valid:
                user_data['voltage'] = voltage
                user_data['step'] = 'config'
                await update.message.reply_text(f"✅ Установлено напряжение: {voltage} В")
                await show_config_menu(update, context)
            else:
                await update.message.reply_text(f"❌ {error_msg}")
        except ValueError:
            await update.message.reply_text("❌ Введите корректное число (например: 3.7)")
    
    elif user_data.get('step') == 'waiting_capacities':
        try:
            # Парсим емкости из текста, поддерживаем разные разделители
            text_clean = text.replace(',', ' ').replace(';', ' ')
            capacities = [int(x) for x in text_clean.split() if x.strip().isdigit()]
            
            required_cells = user_data.get('series', 0) * user_data.get('parallel', 0)
            
            if not required_cells:
                await update.message.reply_text("❌ Сначала настройте конфигурацию (S и P)")
                return
            
            if len(capacities) != required_cells:
                await update.message.reply_text(
                    f"❌ Для конфигурации {user_data['series']}S{user_data['parallel']}P "
                    f"нужно {required_cells} аккумуляторов\n"
                    f"Вы ввели: {len(capacities)}\n\n"
                    f"Введите {required_cells} значений через пробел:"
                )
                return
            
            # Валидация емкостей
            is_valid, error_msg = balancer.validate_capacities(capacities)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ {error_msg}\n\n"
                    f"Пожалуйста, введите корректные значения:"
                )
                return
            
            user_data['capacities'] = capacities
            user_data['step'] = 'config'
            
            await update.message.reply_text(
                f"✅ Введены емкости {len(capacities)} аккумуляторов\n"
                f"📊 Диапазон: {min(capacities)}-{max(capacities)} мАч\n"
                f"📊 Средняя: {sum(capacities)/len(capacities):.0f} мАч"
            )
            await show_config_menu(update, context)
            
        except ValueError as e:
            await update.message.reply_text(
                "❌ Введите корректные числа через пробел\n\n"
                "Пример: 2500 2550 2600 2450 2520 2480 2580 2420"
            )
        except Exception as e:
            logger.error(f"Capacity input error: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке данных. Попробуйте снова."
            )
    
    else:
        # Если сообщение не соответствует ни одному ожидаемому состоянию
        await update.message.reply_text(
            "🤔 Я не понял ваше сообщение. Используйте кнопки меню или команды:\n\n"
            "/start - начать работу\n"
            "/reset - сбросить настройки\n"
            "/status - показать состояние\n"
            "/cancel - отменить операцию\n"
            "/help - помощь"
        )

async def show_config_menu(update, context):
    """Показать меню конфигурации"""
    user_id = update.effective_user.id
    user_data = balancer.user_data.get(user_id, {})
    
    keyboard = [
        [InlineKeyboardButton("🔢 Количество последовательно (S)", callback_data="set_series")],
        [InlineKeyboardButton("🔢 Количество параллельно (P)", callback_data="set_parallel")],
        [InlineKeyboardButton("⚡ Напряжение аккумулятора", callback_data="set_voltage")],
        [InlineKeyboardButton("📝 Ввести емкости", callback_data="set_capacities")],
        [InlineKeyboardButton("📊 Рассчитать сборку", callback_data="calculate")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    config_text = f"""⚙️ Текущая конфигурация:

🔢 Последовательно (S): {user_data.get('series', 'не задано')}
🔢 Параллельно (P): {user_data.get('parallel', 'не задано')}
⚡ Напряжение: {user_data.get('voltage', 3.7)} В
📊 Аккумуляторов: {len(user_data.get('capacities', []))} шт

Выберите параметр для настройки:"""
    
    # Просто используем try-except для определения типа
    try:
        # Если это CallbackQuery
        await update.edit_message_text(config_text, reply_markup=reply_markup)
    except AttributeError:
        # Если это Update
        await update.message.reply_text(config_text, reply_markup=reply_markup)

def main() -> None:
    """Запуск бота"""
    try:
        # Загружаем токен из переменных окружения
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if not token:
            logger.error("Не задан TELEGRAM_BOT_TOKEN в переменных окружения")
            print("❌ ОШИБКА: Не задан токен бота!")
            print("📝 Создайте файл .env с переменной TELEGRAM_BOT_TOKEN")
            print("💡 Или экспортируйте переменную: export TELEGRAM_BOT_TOKEN='ваш_токен'")
            return
        
        application = Application.builder().token(token).build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("reset", reset_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("cancel", cancel_command))
        
        # Обработчики callback запросов (кнопок)
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Обработчики текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        
        # Запуск бота
        logger.info("Бот запущен...")
        print("✅ Бот успешно запущен!")
        print("📱 Используйте команду /start в Telegram для начала работы")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()