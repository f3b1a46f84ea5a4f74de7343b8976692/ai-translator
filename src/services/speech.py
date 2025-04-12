import logging
import os
from gtts import gTTS
from src.config import Config

logger = logging.getLogger(__name__)

class SpeechService:
    def synthesize(self, text: str, output_path: str) -> bool:
        try:
            tts = gTTS(text=text, lang=Config.TARGET_LANGUAGE)
            tts.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Ошибка при синтезе речи: {e}", exc_info=True)
            return False 