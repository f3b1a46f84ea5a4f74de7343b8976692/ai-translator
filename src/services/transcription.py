import logging
import torch
import os
from typing import Optional, Dict, Any, Union
from src.config import Config

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self, use_faster_whisper: bool = True):
        """Инициализирует сервис транскрибации.
        
        Args:
            use_faster_whisper: Использовать ли faster-whisper вместо стандартного whisper
        """
        self.use_faster_whisper = use_faster_whisper
        self.model = self._load_model()
        
    def _load_model(self):
        """Загружает модель для транскрибации.
        
        Returns:
            Модель whisper или faster-whisper
        """
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if self.use_faster_whisper:
            try:
                # Используем faster-whisper для лучшей производительности
                from faster_whisper import WhisperModel
                
                # Определяем compute type в зависимости от устройства
                compute_type = "float16" if device == "cuda" else "int8"
                
                logger.info(f"Загрузка модели Faster Whisper '{Config.WHISPER_MODEL_NAME}' на {device} с compute_type={compute_type}...")
                
                # Проверяем, что директория для моделей существует
                os.makedirs(Config.MODEL_DIR, exist_ok=True)
                
                model = WhisperModel(
                    Config.WHISPER_MODEL_NAME,
                    device=device,
                    compute_type=compute_type,
                    download_root=Config.MODEL_DIR
                )
                
                logger.info(f"Модель Faster Whisper успешно загружена на устройство: {device}")
                return model
                
            except ImportError:
                logger.warning("Библиотека faster-whisper не установлена. Откатываемся к стандартному whisper.")
                self.use_faster_whisper = False
                
        # Используем стандартный whisper, если faster-whisper не доступен
        import whisper
        
        logger.info(f"Загрузка стандартной модели Whisper '{Config.WHISPER_MODEL_NAME}'...")
        model = whisper.load_model(
            Config.WHISPER_MODEL_NAME,
            device=device,
            download_root=Config.MODEL_DIR,
            in_memory=True
        )
        logger.info(f"Стандартная модель Whisper загружена на устройство: {model.device}")
        return model

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Optional[str]:
        """Транскрибирует аудиофайл в текст.
        
        Args:
            audio_path: Путь к аудиофайлу
            language: Код языка аудио (если None, используется язык пользователя)
            
        Returns:
            str | None: Распознанный текст или None в случае ошибки
        """
        try:
            lang = language if language and Config.is_language_supported(language) else Config.TARGET_LANGUAGE
            
            if self.use_faster_whisper:
                # Транскрибация с помощью faster-whisper
                segments, info = self.model.transcribe(
                    audio_path,
                    language=lang,
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                
                # Собираем все сегменты в один текст
                result_text = " ".join([segment.text for segment in segments])
                logger.info(f"Faster Whisper определил язык: {info.language} с вероятностью {info.language_probability:.2f}")
                
                return result_text
            else:
                # Транскрибация с помощью стандартного whisper
                initial_prompt = None
                if lang == 'ru':
                    initial_prompt = "Это голосовое сообщение на русском языке."
                
                result = self.model.transcribe(
                    audio_path,
                    fp16=torch.cuda.is_available(),
                    language=lang,
                    task="transcribe",
                    temperature=0.0,
                    best_of=5,
                    beam_size=5,
                    patience=1.0,
                    condition_on_previous_text=True,
                    initial_prompt=initial_prompt
                )
                return result["text"]
                
        except Exception as e:
            logger.error(f"Ошибка при транскрибации: {e}", exc_info=True)
            return None 