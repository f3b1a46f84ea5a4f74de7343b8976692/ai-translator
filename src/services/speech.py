import logging
import os
from gtts import gTTS
from src.config import Config
from typing import Optional

logger = logging.getLogger(__name__)

class SpeechService:
    def synthesize(self, text: str, output_path: str, language: Optional[str] = None) -> bool:
        """Синтезирует речь из текста и сохраняет в аудиофайл.
        
        Args:
            text: Текст для синтеза
            output_path: Путь к выходному аудиофайлу
            language: Код языка для синтеза (используется Config.TARGET_LANGUAGE, если не указан)
            
        Returns:
            bool: True если синтез успешен, иначе False
        """
        try:
            # Используем указанный язык или язык по умолчанию
            lang = language if language and Config.is_tts_supported(language) else Config.TARGET_LANGUAGE
            
            # Проверяем поддержку TTS для языка
            if not Config.is_tts_supported(lang):
                logger.warning(f"Язык {lang} не поддерживается для синтеза речи, используем {Config.TARGET_LANGUAGE}")
                lang = Config.TARGET_LANGUAGE
                
            tts = gTTS(text=text, lang=lang)
            tts.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Ошибка при синтезе речи: {e}", exc_info=True)
            return False 