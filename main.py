import os
import logging
from bot import Bot

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    # Проверка токена
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден! Установите переменную окружения BOT_TOKEN")
        exit(1)
    
    bot = Bot(BOT_TOKEN)
    print("✅ Бот запускается...")
    bot.run()

if __name__ == "__main__":
    main()