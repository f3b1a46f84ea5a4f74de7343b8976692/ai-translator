import logging
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
from src.config import Config

logger = logging.getLogger(__name__)

class TranslationService:
    def detect_language(self, text: str) -> str | None:
        try:
            lang = detect(text)
            logger.info(f"Определен язык: {lang}")
            return lang
        except LangDetectException:
            logger.warning("Не удалось определить язык")
            return None
        except Exception as e:
            logger.error(f"Ошибка при определении языка: {e}", exc_info=True)
            return None

    def translate(self, text: str, source_lang: str | None = None) -> str | None:
        try:
            source = source_lang if source_lang else 'auto'
            return GoogleTranslator(source=source, target=Config.TARGET_LANGUAGE).translate(text)
        except Exception as e:
            logger.error(f"Ошибка при переводе: {e}", exc_info=True)
            return None 