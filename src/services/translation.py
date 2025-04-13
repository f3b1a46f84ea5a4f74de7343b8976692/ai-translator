import logging
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
from src.config import Config
from typing import Optional

logger = logging.getLogger(__name__)

class TranslationService:
    def detect_language(self, text: str) -> Optional[str]:
        """Определяет язык текста.
        
        Args:
            text: Текст для определения языка
            
        Returns:
            str | None: Код языка или None, если определение не удалось
        """
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

    def translate(
        self, 
        text: str, 
        source_lang: Optional[str] = None, 
        target_lang: Optional[str] = None
    ) -> Optional[str]:
        """Переводит текст с одного языка на другой.
        
        Args:
            text: Текст для перевода
            source_lang: Исходный язык (автоопределение, если None)
            target_lang: Целевой язык (используется Config.TARGET_LANGUAGE, если не указан)
            
        Returns:
            str | None: Переведенный текст или None в случае ошибки
        """
        try:
            source = source_lang if source_lang else 'auto'
            target = target_lang if target_lang and Config.is_language_supported(target_lang) else Config.TARGET_LANGUAGE
            
            # Если исходный и целевой языки совпадают, возвращаем исходный текст
            if source_lang and source_lang == target:
                return text
                
            return GoogleTranslator(source=source, target=target).translate(text)
        except Exception as e:
            logger.error(f"Ошибка при переводе: {e}", exc_info=True)
            return None 