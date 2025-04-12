import logging
import sys
from src import Bot
from src.config import Config

def setup_logging():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=Config.LOG_LEVEL
    )
    # Отключаем логи от telegram
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)

def main():
    try:
        setup_logging()
        bot = Bot()
        bot.setup()
        bot.run()
    except KeyboardInterrupt:
        logging.info("Получен сигнал прерывания. Завершаем работу...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()