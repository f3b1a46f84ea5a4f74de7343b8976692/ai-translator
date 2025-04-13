import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TARGET_LANGUAGE = 'en'
    WHISPER_MODEL_NAME = "large-v3"
    MODEL_DIR = os.getenv("MODEL_DIR", "./models")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Поддерживаемые языки для перевода и синтеза
    SUPPORTED_LANGUAGES = {
        'ar': 'арабский',
        'bg': 'болгарский',
        'cs': 'чешский',
        'da': 'датский',
        'de': 'немецкий',
        'el': 'греческий',
        'en': 'английский',
        'es': 'испанский',
        'et': 'эстонский',
        'fa': 'персидский',
        'fi': 'финский',
        'fr': 'французский',
        'he': 'иврит',
        'hi': 'хинди',
        'hr': 'хорватский',
        'hu': 'венгерский',
        'id': 'индонезийский',
        'it': 'итальянский',
        'ja': 'японский',
        'ko': 'корейский',
        'lt': 'литовский',
        'lv': 'латышский',
        'ms': 'малайский',
        'nl': 'нидерландский',
        'no': 'норвежский',
        'pl': 'польский',
        'pt': 'португальский',
        'ro': 'румынский',
        'ru': 'русский',
        'sk': 'словацкий',
        'sl': 'словенский',
        'sq': 'албанский',
        'sv': 'шведский',
        'th': 'тайский',
        'tr': 'турецкий',
        'uk': 'украинский',
        'vi': 'вьетнамский',
        'zh': 'китайский',
    }
    
    # Названия языков на их родных языках
    NATIVE_LANGUAGE_NAMES = {
        'ar': 'العربية',
        'bg': 'Български',
        'cs': 'Čeština',
        'da': 'Dansk',
        'de': 'Deutsch',
        'el': 'Ελληνικά',
        'en': 'English',
        'es': 'Español',
        'et': 'Eesti',
        'fa': 'فارسی',
        'fi': 'Suomi',
        'fr': 'Français',
        'he': 'עברית',
        'hi': 'हिन्दी',
        'hr': 'Hrvatski',
        'hu': 'Magyar',
        'id': 'Bahasa Indonesia',
        'it': 'Italiano',
        'ja': '日本語',
        'ko': '한국어',
        'lt': 'Lietuvių',
        'lv': 'Latviešu',
        'ms': 'Bahasa Melayu',
        'nl': 'Nederlands',
        'no': 'Norsk',
        'pl': 'Polski',
        'pt': 'Português',
        'ro': 'Română',
        'ru': 'Русский',
        'sk': 'Slovenčina',
        'sl': 'Slovenščina',
        'sq': 'Shqip',
        'sv': 'Svenska',
        'th': 'ไทย',
        'tr': 'Türkçe',
        'uk': 'Українська',
        'vi': 'Tiếng Việt',
        'zh': '中文',
    }
    
    # Языки с поддержкой синтеза речи
    # Основано на поддержке gTTS
    TTS_SUPPORTED_LANGUAGES = {
        'ar': 'арабский',
        'bg': 'болгарский',
        'cs': 'чешский',
        'da': 'датский',
        'de': 'немецкий',
        'el': 'греческий',
        'en': 'английский',
        'es': 'испанский',
        'et': 'эстонский',
        'fi': 'финский',
        'fr': 'французский',
        'hi': 'хинди',
        'hr': 'хорватский',
        'hu': 'венгерский',
        'id': 'индонезийский',
        'it': 'итальянский',
        'ja': 'японский',
        'ko': 'корейский',
        'lt': 'литовский',
        'lv': 'латышский',
        'nl': 'нидерландский',
        'no': 'норвежский',
        'pl': 'польский',
        'pt': 'португальский',
        'ro': 'румынский',
        'ru': 'русский',
        'sk': 'словацкий',
        'sv': 'шведский',
        'th': 'тайский',
        'tr': 'турецкий',
        'uk': 'украинский',
        'vi': 'вьетнамский',
        'zh': 'китайский',
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
        'SA': 'ar', 'AE': 'ar', 'EG': 'ar',
        'UA': 'uk', 'BG': 'bg',
        'CZ': 'cs', 'DK': 'da',
        'GR': 'el', 'EE': 'et',
        'IR': 'fa', 'FI': 'fi', 
        'IL': 'he', 'IN': 'hi',
        'HR': 'hr', 'HU': 'hu',
        'ID': 'id', 'MY': 'ms',
        'NL': 'nl', 'NO': 'no',
        'PL': 'pl', 'RO': 'ro',
        'SK': 'sk', 'SI': 'sl',
        'AL': 'sq', 'SE': 'sv',
        'TH': 'th', 'TR': 'tr',
        'VN': 'vi'
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
    
    # Сообщения для подтверждения языка перевода
    TRANSLATION_CONFIRM_MESSAGES = {
        'en': "🔊 I detected your message in {source_lang}. Which language would you like to hear it in?",
        'ru': "🔊 Я обнаружил, что ваше сообщение на языке {source_lang}. На каком языке вы хотите его прослушать?",
        'es': "🔊 Detecté que tu mensaje está en {source_lang}. ¿En qué idioma te gustaría escucharlo?",
        'fr': "🔊 J'ai détecté que votre message est en {source_lang}. Dans quelle langue souhaitez-vous l'écouter?",
        'de': "🔊 Ich habe erkannt, dass Ihre Nachricht in {source_lang} ist. In welcher Sprache möchten Sie sie hören?",
        'it': "🔊 Ho rilevato che il tuo messaggio è in {source_lang}. In quale lingua vorresti ascoltarlo?",
        'pt': "🔊 Detectei que sua mensagem está em {source_lang}. Em qual idioma você gostaria de ouvi-la?",
        'zh': "🔊 我检测到您的消息是{source_lang}语。您希望用哪种语言收听它？",
        'ja': "🔊 あなたのメッセージは{source_lang}であることを検出しました。どの言語で聞きたいですか？",
        'ko': "🔊 메시지가 {source_lang}로 감지되었습니다. 어떤 언어로 듣고 싶으신가요?",
        'ar': "🔊 لقد اكتشفت أن رسالتك باللغة {source_lang}. بأي لغة ترغب في الاستماع إليها؟"
    }
    
    # Сообщения о процессе перевода
    TRANSLATING_MESSAGES = {
        'en': "Translating to {target_lang}... Your audio will be ready soon.",
        'ru': "Перевод на {target_lang}... Ваше аудио будет готово в ближайшее время.",
        'es': "Traduciendo al {target_lang}... Tu audio estará listo pronto.",
        'fr': "Traduction en {target_lang}... Votre audio sera bientôt prêt.",
        'de': "Übersetzung ins {target_lang}... Ihre Audiodatei wird in Kürze fertig sein.",
        'it': "Traduzione in {target_lang}... Il tuo audio sarà pronto a breve.",
        'pt': "Traduzindo para {target_lang}... Seu áudio estará pronto em breve.",
        'zh': "正在翻译成{target_lang}...您的音频很快就会准备好。",
        'ja': "{target_lang}に翻訳中...あなたの音声はまもなく準備ができます。",
        'ko': "{target_lang}(으)로 번역 중... 오디오가 곧 준비됩니다.",
        'ar': "الترجمة إلى {target_lang}... سيكون الصوت الخاص بك جاهزًا قريبًا."
    }
    
    # Заголовки для текстового перевода
    TRANSLATION_HEADERS = {
        'en': '📝 Translation:', 
        'es': '📝 Traducción:', 
        'fr': '📝 Traduction:',
        'de': '📝 Übersetzung:', 
        'it': '📝 Traduzione:', 
        'pt': '📝 Tradução:',
        'ar': '📝 الترجمة:', 
        'ja': '📝 翻訳:', 
        'zh': '📝 翻译:',
        'ko': '📝 번역:',
        'ru': '📝 Перевод:'
    }
    
    # Подписи для аудио перевода
    AUDIO_CAPTIONS = {
        'en': '🔊 Audio translation', 
        'es': '🔊 Traducción de audio', 
        'fr': '🔊 Traduction audio',
        'de': '🔊 Audio-Übersetzung', 
        'it': '🔊 Traduzione audio', 
        'pt': '🔊 Tradução de áudio',
        'ar': '🔊 الترجمة الصوتية', 
        'ja': '🔊 音声翻訳', 
        'zh': '🔊 语音翻译',
        'ko': '🔊 음성 번역',
        'ru': '🔊 Озвученный перевод'
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
    def get_native_language_name(cls, lang_code: str) -> str:
        """Получить название языка на родном языке.
        
        Args:
            lang_code: Код языка
            
        Returns:
            Название языка на родном языке или код языка, если название не найдено
        """
        return cls.NATIVE_LANGUAGE_NAMES.get(lang_code, lang_code)
        
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
            Код языка пользователя или DEFAULT_LANGUAGE по умолчанию
        """
        return cls.USER_LANGUAGE_PREFS.get(user_id, cls.TARGET_LANGUAGE) 