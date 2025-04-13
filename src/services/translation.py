import logging
from langdetect import detect, LangDetectException
import langid
from deep_translator import GoogleTranslator
from src.config import Config
from typing import Optional, Tuple, Dict, List
import re

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        """Инициализирует сервис перевода."""
        # Настройка langid для работы со всеми поддерживаемыми языками
        langid.set_languages(list(Config.SUPPORTED_LANGUAGES.keys()))
    
    def detect_language(self, text: str, hint_language: Optional[str] = None) -> Optional[str]:
        """Определяет язык текста с использованием нескольких методов для повышения точности.
        
        Args:
            text: Текст для определения языка
            hint_language: Предполагаемый язык (например, определенный Whisper), 
                           который имеет высокий приоритет
            
        Returns:
            str | None: Код языка или None, если определение не удалось
        """
        # Если передан предполагаемый язык и он поддерживается, возвращаем его
        if hint_language and Config.is_language_supported(hint_language):
            logger.info(f"Используем предполагаемый язык: {hint_language} (из внешнего источника)")
            return hint_language
            
        if not text or len(text.strip()) < 3:
            logger.warning("Текст слишком короткий для надежного определения языка")
            return None
            
        try:
            # Очищаем текст от URL, эмодзи и других специальных символов
            cleaned_text = self._clean_text_for_detection(text)
            if not cleaned_text or len(cleaned_text.strip()) < 3:
                logger.warning("После очистки текст слишком короткий для определения языка")
                return None
                
            # Используем несколько методов определения языка
            langdetect_result = self._detect_with_langdetect(cleaned_text)
            langid_result = self._detect_with_langid(cleaned_text)
            
            # Объединяем результаты для более точного определения
            final_lang = self._combine_detection_results(
                text=cleaned_text,
                langdetect_result=langdetect_result, 
                langid_result=langid_result,
                hint_language=hint_language
            )
            
            if final_lang and Config.is_language_supported(final_lang):
                logger.info(f"Определен язык: {final_lang} (langdetect: {langdetect_result}, langid: {langid_result})")
                return final_lang
            else:
                logger.warning(f"Определенный язык {final_lang} не поддерживается")
                
                # Проверяем, можно ли использовать предполагаемый язык в качестве запасного варианта
                if hint_language:
                    logger.info(f"Используем предполагаемый язык {hint_language} в качестве запасного варианта")
                    return hint_language
                    
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при определении языка: {e}", exc_info=True)
            
            # В случае ошибки можно использовать предполагаемый язык как запасной вариант
            if hint_language:
                logger.info(f"Из-за ошибки используем предполагаемый язык {hint_language}")
                return hint_language
                
            return None
    
    def _clean_text_for_detection(self, text: str) -> str:
        """Очищает текст от шума для более точного определения языка.
        
        Args:
            text: Исходный текст
            
        Returns:
            str: Очищенный текст
        """
        # Удаляем URL
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Удаляем эмодзи
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # эмоциональные
            "\U0001F300-\U0001F5FF"  # символы и пиктограммы
            "\U0001F680-\U0001F6FF"  # транспорт и символы
            "\U0001F700-\U0001F77F"  # алхимические символы
            "\U0001F780-\U0001F7FF"  # геометрические фигуры
            "\U0001F800-\U0001F8FF"  # дополнительные стрелки
            "\U0001F900-\U0001F9FF"  # дополнительные символы
            "\U0001FA00-\U0001FA6F"  # символы шахмат
            "\U0001FA70-\U0001FAFF"  # символы эмодзи
            "\U00002702-\U000027B0"  # декоративные символы
            "\U000024C2-\U0001F251" 
            "]+", flags=re.UNICODE
        )
        text = emoji_pattern.sub(r'', text)
        
        # Удаляем повторяющиеся пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _detect_with_langdetect(self, text: str) -> Optional[str]:
        """Определяет язык с помощью библиотеки langdetect.
        
        Args:
            text: Текст для определения
            
        Returns:
            str | None: Код языка или None в случае ошибки
        """
        try:
            return detect(text)
        except LangDetectException:
            return None
        except Exception:
            return None
    
    def _detect_with_langid(self, text: str) -> Optional[str]:
        """Определяет язык с помощью библиотеки langid.
        
        Args:
            text: Текст для определения
            
        Returns:
            str | None: Код языка или None в случае ошибки
        """
        try:
            lang, confidence = langid.classify(text)
            if confidence > 0.5:  # Минимальный порог уверенности
                return lang
            return None
        except Exception:
            return None
    
    def _combine_detection_results(
        self, 
        text: str,
        langdetect_result: Optional[str], 
        langid_result: Optional[str],
        hint_language: Optional[str] = None
    ) -> Optional[str]:
        """Объединяет результаты различных методов определения языка.
        
        Args:
            text: Исходный текст
            langdetect_result: Результат от langdetect
            langid_result: Результат от langid
            hint_language: Предполагаемый язык (необязательно)
            
        Returns:
            str | None: Итоговый код языка или None
        """
        # Если есть предполагаемый язык и он совпадает с одним из результатов, возвращаем его
        if hint_language:
            if hint_language == langdetect_result or hint_language == langid_result:
                logger.info(f"Предполагаемый язык {hint_language} подтвержден одним из методов определения")
                return hint_language
        
        # Если оба метода согласны - возвращаем этот результат
        if langdetect_result and langid_result and langdetect_result == langid_result:
            return langdetect_result
            
        # Если только один метод дал результат - используем его
        if langdetect_result and not langid_result:
            return langdetect_result
        if not langdetect_result and langid_result:
            return langid_result
            
        # Если результаты разные, проверяем наличие характерных символов
        if langdetect_result and langid_result:
            # Проверка на китайские символы
            if re.search(r'[\u4e00-\u9fff]', text):
                return 'zh'
            # Проверка на японские символы (хирагана, катакана)
            if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
                return 'ja'
            # Проверка на корейские символы (хангыль)
            if re.search(r'[\uac00-\ud7af\u1100-\u11ff]', text):
                return 'ko'
            # Проверка на арабский
            if re.search(r'[\u0600-\u06ff]', text):
                return 'ar'
            # Проверка на кириллицу
            if re.search(r'[а-яА-Я]', text):
                # Если есть кириллица и один из результатов русский - выбираем русский
                if langdetect_result == 'ru' or langid_result == 'ru':
                    return 'ru'
                # Если один из результатов украинский, болгарский или сербский - выбираем его
                for lang in ['uk', 'bg', 'sr']:
                    if langdetect_result == lang or langid_result == lang:
                        return lang
                # Иначе по умолчанию выбираем русский для кириллицы
                return 'ru'

            # Проверка на греческие символы
            if re.search(r'[\u0370-\u03ff]', text):
                return 'el'
                
            # Если есть предполагаемый язык, используем его при конфликте
            if hint_language:
                return hint_language
                
            # По умолчанию приоритет отдаем langdetect
            return langdetect_result
            
        # Если оба метода вернули None, но есть предполагаемый язык, используем его
        if hint_language:
            return hint_language
            
        # Если оба метода вернули None и нет предполагаемого языка - не удалось определить язык
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