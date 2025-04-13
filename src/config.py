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
        'ru': 'русский',
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
        'ru': 'русский',
    }
    
    # Маппинг кодов стран в коды языков
    COUNTRY_TO_LANGUAGE = {
        'US': 'en', 'GB': 'en', 'AU': 'en', 'CA': 'en',
        'RU': 'ru', 'BY': 'ru', 'KZ': 'ru',
        'ES': 'es', 'MX': 'es', 'CO': 'es', 'AR': 'es',
        'FR': 'fr', 'DE': 'de', 'IT': 'it', 
        'BR': 'pt', 'PT': 'pt',
        'CN': 'zh', 'TW': 'zh', 'HK': 'zh',
        'JP': 'ja', 'KR': 'ko',
        'SA': 'ar', 'AE': 'ar', 'EG': 'ar'
    }
    
    # Приветственные сообщения на разных языках
    WELCOME_MESSAGES = {
        'en': "Hello! I support the following languages:\n{languages}\n\nSend me a text or voice message in any of these languages, and I'll translate it to your preferred language.",
        'ru': "Привет! Я поддерживаю следующие языки:\n{languages}\n\nОтправь мне текстовое или голосовое сообщение на любом из этих языков, и я переведу его на твой предпочитаемый язык.",
        'es': "¡Hola! Admito los siguientes idiomas:\n{languages}\n\nEnvíame un mensaje de texto o de voz en cualquiera de estos idiomas y lo traduciré a tu idioma preferido.",
        'fr': "Bonjour! Je prends en charge les langues suivantes:\n{languages}\n\nEnvoyez-moi un message texte ou vocal dans l'une de ces langues, et je le traduirai dans votre langue préférée.",
        'de': "Hallo! Ich unterstütze die folgenden Sprachen:\n{languages}\n\nSenden Sie mir eine Text- oder Sprachnachricht in einer dieser Sprachen, und ich werde sie in Ihre bevorzugte Sprache übersetzen.",
        'it': "Ciao! Supporto le seguenti lingue:\n{languages}\n\nInviami un messaggio di testo o vocale in una di queste lingue e lo tradurrò nella tua lingua preferita.",
        'pt': "Olá! Eu suporto os seguintes idiomas:\n{languages}\n\nEnvie-me uma mensagem de texto ou de voz em qualquer um desses idiomas, e eu a traduzirei para o seu idioma preferido.",
        'zh': "你好！我支持以下语言：\n{languages}\n\n用这些语言中的任何一种向我发送文本或语音消息，我会将其翻译成你喜欢的语言。",
        'ja': "こんにちは！次の言語をサポートしています：\n{languages}\n\nこれらの言語のいずれかでテキストメッセージまたは音声メッセージを送信してください。あなたの希望する言語に翻訳します。",
        'ko': "안녕하세요! 저는 다음 언어를 지원합니다:\n{languages}\n\n이러한 언어 중 하나로 텍스트 또는 음성 메시지를 보내주시면 선호하는 언어로 번역해 드리겠습니다.",
        'ar': "مرحبًا! أنا أدعم اللغات التالية:\n{languages}\n\nأرسل لي رسالة نصية أو صوتية بأي من هذه اللغات، وسأترجمها إلى لغتك المفضلة."
    }

    # Словарь предпочтений пользователей по языкам
    # Будет заполняться в формате {user_id: language_code}
    USER_LANGUAGE_PREFS = {}
    
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
        
    @classmethod
    def get_language_from_country(cls, country_code: str) -> str:
        """Получить предпочтительный язык по коду страны.
        
        Args:
            country_code: Двухбуквенный код страны (ISO 3166-1 alpha-2)
            
        Returns:
            Код языка или 'en' по умолчанию
        """
        return cls.COUNTRY_TO_LANGUAGE.get(country_code.upper(), 'en')
        
    @classmethod
    def set_user_language(cls, user_id: int, language_code: str) -> None:
        """Установить предпочтительный язык пользователя.
        
        Args:
            user_id: ID пользователя в Telegram
            language_code: Код предпочтительного языка
        """
        if cls.is_language_supported(language_code):
            cls.USER_LANGUAGE_PREFS[user_id] = language_code
            
    @classmethod
    def get_user_language(cls, user_id: int) -> str:
        """Получить предпочтительный язык пользователя.
        
        Args:
            user_id: ID пользователя в Telegram
            
        Returns:
            Код языка пользователя или 'ru' по умолчанию
        """
        return cls.USER_LANGUAGE_PREFS.get(user_id, cls.TARGET_LANGUAGE) 