import logging
import torch
import whisper
from src.config import Config

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        self.model = self._load_model()
        
    def _load_model(self):
        logger.info(f"Загрузка модели Whisper '{Config.WHISPER_MODEL_NAME}'...")
        model = whisper.load_model(
            Config.WHISPER_MODEL_NAME,
            device="cuda" if torch.cuda.is_available() else "cpu",
            download_root=Config.MODEL_DIR,
            in_memory=True
        )
        logger.info(f"Модель Whisper загружена на устройство: {model.device}")
        return model

    def transcribe(self, audio_path: str) -> str | None:
        try:
            result = self.model.transcribe(
                audio_path,
                fp16=torch.cuda.is_available(),
                language=Config.TARGET_LANGUAGE,
                task="transcribe",
                temperature=0.0,
                best_of=5,
                beam_size=5,
                patience=1.0,
                condition_on_previous_text=True,
                initial_prompt="Это голосовое сообщение на русском языке."
            )
            return result["text"]
        except Exception as e:
            logger.error(f"Ошибка при транскрибации: {e}", exc_info=True)
            return None 