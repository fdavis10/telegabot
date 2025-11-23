import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, form, admin
from aiogram.client.default import DefaultBotProperties
from database.db import init_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # Инициализируем базу данных ОДИН раз
    init_db()
    
    # Создаем бота и диспетчер ОДИН раз
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # Подключаем роутеры ОДИН раз (admin.router должен быть первым)
    dp.include_routers(admin.router, start.router, form.router)

    logger.info("🤖 Бот запущен...")
    
    try:
        # Запускаем polling (он сам бесконечный)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        # Закрываем сессию бота при завершении
        await bot.session.close()
        logger.info("🛑 Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске: {e}")