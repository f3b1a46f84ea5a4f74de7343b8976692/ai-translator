import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TARGET_LANGUAGE = 'ru'
    WHISPER_MODEL_NAME = "large-v3"
    MODEL_DIR = os.getenv("MODEL_DIR", "./models")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Поддерживаемые языки для перевода и синтеза
    SUPPORTED_LANGUAGES = {
        'ar': 'арабский',
        'ja': 'японский',
        'en': 'английский',
        'es': 'испанский',
        'fr': 'французский',
        'de': 'немецкий',
        'it': 'итальянский',
        'pt': 'португальский',
        'zh': 'китайский',
        'ko': 'корейский',
    }
    
    # Языки с поддержкой синтеза речи
    TTS_SUPPORTED_LANGUAGES = {
        'ar': 'арабский',
        'ja': 'японский',
        'en': 'английский',
        'es': 'испанский',
        'fr': 'французский',
        'de': 'немецкий',
        'it': 'итальянский',
        'pt': 'португальский',
        'zh': 'китайский',
        'ko': 'корейский',
    }
    
    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен")
            
    @classmethod
    def is_language_supported(cls, lang_code: str) -> bool:
        return lang_code in cls.SUPPORTED_LANGUAGES
        
    @classmethod
    def is_tts_supported(cls, lang_code: str) -> bool:
        return lang_code in cls.TTS_SUPPORTED_LANGUAGES
        
    @classmethod
    def get_language_name(cls, lang_code: str) -> str:
        return cls.SUPPORTED_LANGUAGES.get(lang_code, lang_code) 