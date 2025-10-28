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
    while True:
        try:
            # Инициализируем базу данных
            init_db()
            
            bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
            dp = Dispatcher()

            # ВАЖНО: admin.router должен быть первым для обработки команд с высшим приоритетом
            dp.include_routers(admin.router, start.router, form.router)

            logger.info("🤖 Бот запущен...")
            await dp.start_polling(bot)
            
        except Exception as e:
            logger.error(f"❌ Бот упал с ошибкой: {e}")
            logger.info("🔄 Перезапуск через 5 секунд...")
            await asyncio.sleep(5)
        finally:
            # Закрываем сессию бота при любом исходе
            try:
                await bot.session.close()
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())