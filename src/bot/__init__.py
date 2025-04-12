import logging
import asyncio
import signal
import sys
from telegram.ext import ApplicationBuilder
from telegram.error import Conflict
from src.config import Config
from src.bot.handlers import BotHandlers

logger = logging.getLogger(__name__)

class Bot:
    def __init__(self):
        Config.validate()
        self.application = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()
        self.handlers = BotHandlers()
        self._shutdown_event = asyncio.Event()

    def setup(self):
        for handler in self.handlers.get_handlers():
            self.application.add_handler(handler)
        
        # Устанавливаем обработчики сигналов
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info(f"Получен сигнал {signum}. Начинаем graceful shutdown...")
        self._shutdown_event.set()

    async def _run(self):
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Бот успешно запущен")
            
            # Ждем сигнала завершения
            await self._shutdown_event.wait()
            
            logger.info("Останавливаем бота...")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            
        except Conflict as e:
            logger.error(f"Конфликт: {e}. Убедитесь, что не запущено несколько экземпляров бота.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
            sys.exit(1)

    def run(self):
        logger.info("Запуск бота...")
        asyncio.run(self._run()) 