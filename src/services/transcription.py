import logging
import torch
import os
from typing import Optional, Dict, Any, Union, Tuple
from src.config import Config
import whisper
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self, use_faster_whisper: bool = True):
        """Инициализация сервиса транскрибации.
        
        Args:
            use_faster_whisper: Использовать ли faster-whisper вместо обычного whisper
        """
        self.use_faster_whisper = use_faster_whisper
        self.model = self._load_model()
        logger.info(f"Сервис транскрибации инициализирован с {'faster-whisper' if use_faster_whisper else 'whisper'}")
        
    def _load_model(self):
        """Загружает модель для транскрибации.
        
        Returns:
            Загруженная модель whisper или faster-whisper
        """
        # Создаем директорию для моделей, если она не существует
        os.makedirs(Config.MODEL_DIR, exist_ok=True)
        
        model_name = os.getenv("WHISPER_MODEL", Config.WHISPER_MODEL_NAME)
        
        if self.use_faster_whisper:
            # Определяем, есть ли доступная CUDA
            compute_type = "float16" if torch.cuda.is_available() else "int8"
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Загружаем модель faster-whisper
            model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
                download_root=Config.MODEL_DIR
            )
            
            logger.info(f"Faster Whisper модель {model_name} загружена на устройство: {device}, тип вычислений: {compute_type}")
            return model
        else:
            # Загружаем стандартную модель whisper
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = whisper.load_model(model_name, device=device, download_root=Config.MODEL_DIR)
            
            logger.info(f"Стандартная модель Whisper загружена на устройство: {model.device}")
            return model

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Union[str, Tuple[str, Optional[str]]]:
        """Транскрибирует аудиофайл в текст и возвращает определенный язык.
        
        Args:
            audio_path: Путь к аудиофайлу
            language: Код языка аудио (если None, используется язык пользователя)
            
        Returns:
            str | Tuple[str, Optional[str]]: Распознанный текст или кортеж (текст, определенный_язык)
        """
        try:
            # Получаем список всех поддерживаемых языков для Whisper
            whisper_langs = self._get_whisper_supported_languages()
            
            # Преобразуем переданный код языка в код, поддерживаемый Whisper
            lang = None
            if language and language in whisper_langs:
                lang = language
            elif language and language not in whisper_langs:
                # Для некоторых языков используем близкие варианты
                lang_mapping = {
                    'ms': 'id',  # малайский → индонезийский
                    'no': 'da',  # норвежский → датский
                    'et': 'fi',  # эстонский → финский
                    'lv': 'lt',  # латышский → литовский
                    'sq': 'hr',  # албанский → хорватский
                    'sl': 'hr',  # словенский → хорватский
                    'sk': 'cs',  # словацкий → чешский
                }
                lang = lang_mapping.get(language)
                if lang:
                    logger.info(f"Используем близкий язык {lang} вместо {language} для распознавания речи")
                else:
                    logger.warning(f"Язык {language} не поддерживается Whisper напрямую и не имеет замены")
            
            if self.use_faster_whisper:
                # Транскрибация с помощью faster-whisper
                segments, info = self.model.transcribe(
                    audio_path,
                    language=lang,  # Если lang=None, то language detection
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                
                # Собираем все сегменты в один текст
                result_text = " ".join([segment.text for segment in segments])
                detected_lang = info.language
                probability = info.language_probability
                
                logger.info(f"Faster Whisper определил язык: {detected_lang} с вероятностью {probability:.2f}")
                
                # Проверяем, является ли обнаруженный язык поддерживаемым в нашем приложении
                if detected_lang and not Config.is_language_supported(detected_lang):
                    # Пытаемся найти код языка, который мы поддерживаем
                    for supported_lang in Config.SUPPORTED_LANGUAGES.keys():
                        if supported_lang[:2] == detected_lang[:2]:
                            logger.info(f"Whisper определил {detected_lang}, используем совместимый код {supported_lang}")
                            detected_lang = supported_lang
                            break
                
                return result_text, detected_lang
            else:
                # Транскрибация с помощью стандартного whisper
                options = {"language": lang} if lang else {}
                
                # Если язык не передан, то определяем автоматически
                if not lang:
                    options["task"] = "transcribe"
                
                result = self.model.transcribe(audio_path, **options)
                detected_lang = result.get("language")
                
                logger.info(f"Whisper определил язык: {detected_lang}")
                
                return result["text"], detected_lang
        except Exception as e:
            logger.error(f"Ошибка при транскрибации: {e}", exc_info=True)
            return None
            
    def _get_whisper_supported_languages(self) -> Dict[str, str]:
        """Возвращает словарь языков, поддерживаемых Whisper.
        
        Returns:
            Dict[str, str]: Словарь с кодами и названиями языков
        """
        # Whisper поддерживает следующие языки
        # (этот список основан на документации whisper)
        return {
            'en': 'english',
            'zh': 'chinese',
            'de': 'german',
            'es': 'spanish',
            'ru': 'russian',
            'ko': 'korean',
            'fr': 'french',
            'ja': 'japanese',
            'pt': 'portuguese',
            'tr': 'turkish',
            'pl': 'polish',
            'ca': 'catalan',
            'nl': 'dutch',
            'ar': 'arabic',
            'sv': 'swedish',
            'it': 'italian',
            'id': 'indonesian',
            'hi': 'hindi',
            'fi': 'finnish',
            'vi': 'vietnamese',
            'he': 'hebrew',
            'uk': 'ukrainian',
            'el': 'greek',
            'ms': 'malay',
            'cs': 'czech',
            'ro': 'romanian',
            'da': 'danish',
            'hu': 'hungarian',
            'ta': 'tamil',
            'no': 'norwegian',
            'th': 'thai',
            'ur': 'urdu',
            'hr': 'croatian',
            'bg': 'bulgarian',
            'lt': 'lithuanian',
            'la': 'latin',
            'mi': 'maori',
            'ml': 'malayalam',
            'cy': 'welsh',
            'sk': 'slovak',
            'te': 'telugu',
            'fa': 'persian',
            'lv': 'latvian',
            'bn': 'bengali',
            'sr': 'serbian',
            'az': 'azerbaijani',
            'sl': 'slovenian',
            'kn': 'kannada',
            'et': 'estonian',
            'mk': 'macedonian',
            'br': 'breton',
            'eu': 'basque',
            'is': 'icelandic',
            'hy': 'armenian',
            'ne': 'nepali',
            'mn': 'mongolian',
            'bs': 'bosnian',
            'kk': 'kazakh',
            'sq': 'albanian',
            'sw': 'swahili',
            'gl': 'galician',
            'mr': 'marathi',
            'pa': 'punjabi',
            'si': 'sinhala',
            'km': 'khmer',
            'sn': 'shona',
            'yo': 'yoruba',
            'so': 'somali',
            'af': 'afrikaans',
            'oc': 'occitan',
            'ka': 'georgian',
            'be': 'belarusian',
            'tg': 'tajik',
            'sd': 'sindhi',
            'gu': 'gujarati',
            'am': 'amharic',
            'yi': 'yiddish',
            'lo': 'lao',
            'uz': 'uzbek',
            'fo': 'faroese',
            'ht': 'haitian creole',
            'ps': 'pashto',
            'tk': 'turkmen',
            'nn': 'nynorsk',
            'mt': 'maltese',
            'sa': 'sanskrit',
            'lb': 'luxembourgish',
            'my': 'myanmar',
            'bo': 'tibetan',
            'tl': 'tagalog',
            'mg': 'malagasy',
            'as': 'assamese',
            'tt': 'tatar',
            'haw': 'hawaiian',
            'ln': 'lingala',
            'ha': 'hausa',
            'ba': 'bashkir',
            'jw': 'javanese',
            'su': 'sundanese',
        } 