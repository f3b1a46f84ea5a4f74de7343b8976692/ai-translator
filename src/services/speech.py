import logging
import os
import tempfile
from gtts import gTTS
from src.config import Config
from typing import Optional, Dict, Tuple, List, Any
import subprocess
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class TTSEngine(ABC):
    """Абстрактный базовый класс для движков синтеза речи."""
    
    @abstractmethod
    def synthesize(self, text: str, output_path: str, language: str) -> bool:
        """Синтезирует речь из текста и сохраняет в аудиофайл.
        
        Args:
            text: Текст для синтеза
            output_path: Путь к выходному аудиофайлу
            language: Код языка для синтеза
            
        Returns:
            bool: True если синтез успешен, иначе False
        """
        pass
        
    @abstractmethod
    def supports_language(self, language: str) -> bool:
        """Проверяет, поддерживает ли движок указанный язык.
        
        Args:
            language: Код языка
            
        Returns:
            bool: True если язык поддерживается, иначе False
        """
        pass

class GTTSEngine(TTSEngine):
    """Движок синтеза речи на основе Google Text-to-Speech."""
    
    def __init__(self):
        """Инициализирует движок Google TTS."""
        self.supported_languages = Config.TTS_SUPPORTED_LANGUAGES.keys()
        
        # Специальные настройки для разных языков
        self.language_settings = {
            'ar': {'slow': True, 'tld': 'com.sa'},  # Арабский - медленнее и использовать сервер Саудовской Аравии
            'zh': {'tld': 'com.cn'},  # Китайский - использовать китайский сервер
            'ja': {'tld': 'co.jp'},  # Японский - использовать японский сервер
            'ko': {'tld': 'co.kr'},  # Корейский - использовать корейский сервер
            'ru': {'tld': 'ru'},     # Русский - использовать российский сервер
        }
        
    def supports_language(self, language: str) -> bool:
        """Проверяет, поддерживает ли Google TTS указанный язык.
        
        Args:
            language: Код языка
            
        Returns:
            bool: True если язык поддерживается, иначе False
        """
        return language in self.supported_languages
        
    def synthesize(self, text: str, output_path: str, language: str) -> bool:
        """Синтезирует речь с помощью Google TTS.
        
        Args:
            text: Текст для синтеза
            output_path: Путь к выходному аудиофайлу
            language: Код языка для синтеза
            
        Returns:
            bool: True если синтез успешен, иначе False
        """
        try:
            # Проверяем, поддерживается ли язык
            if not self.supports_language(language):
                logger.warning(f"Язык {language} не поддерживается Google TTS, используем {Config.TARGET_LANGUAGE}")
                language = Config.TARGET_LANGUAGE
            
            # Получаем специальные настройки для языка, если они есть
            settings = self.language_settings.get(language, {})
            slow = settings.get('slow', False)
            tld = settings.get('tld', 'com')
            
            logger.info(f"Синтез речи для языка {language} с настройками: slow={slow}, tld={tld}")
                
            # Создаем объект gTTS с указанным языком и настройками
            tts = gTTS(
                text=text, 
                lang=language, 
                slow=slow,
                tld=tld
            )
            
            # Гарантируем, что директория существует
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Сохраняем аудио
            tts.save(output_path)
            logger.info(f"Google TTS: Аудио успешно сгенерировано на языке {language} и сохранено в {output_path}")
            
            # Проверяем, нужна ли пост-обработка аудио (например, нормализация громкости)
            self._post_process_audio(output_path, language)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при синтезе речи с Google TTS: {e}", exc_info=True)
            return False
            
    def _post_process_audio(self, file_path: str, language: str) -> None:
        """Выполняет дополнительную обработку сгенерированного аудио.
        
        Args:
            file_path: Путь к аудиофайлу
            language: Код языка
        """
        try:
            # Для некоторых языков, где gTTS может генерировать тихий звук,
            # нормализуем громкость используя ffmpeg
            if language in ['ar', 'zh', 'ja']:
                temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                temp_path = temp_file.name
                temp_file.close()
                
                # Нормализация громкости с помощью ffmpeg
                cmd = [
                    'ffmpeg',
                    '-y',  # Перезаписать выходной файл без подтверждения
                    '-i', file_path,  # Входной файл
                    '-af', 'loudnorm=I=-16:LRA=11:TP=-1.5',  # Нормализация громкости
                    '-ar', '44100',  # Частота дискретизации
                    temp_path  # Временный выходной файл
                ]
                
                subprocess.run(cmd, check=True, capture_output=True)
                
                # Заменяем оригинальный файл обработанным
                os.replace(temp_path, file_path)
                logger.info(f"Аудио файл {file_path} успешно обработан с нормализацией громкости")
                
        except Exception as e:
            logger.warning(f"Ошибка при пост-обработке аудио: {e}")
            # Не прерываем выполнение, если пост-обработка не удалась

class SpeechService:
    """Сервис для синтеза речи с использованием разных движков в зависимости от языка."""
    
    def __init__(self):
        """Инициализирует сервис синтеза речи со всеми доступными движками."""
        # Инициализируем доступные движки
        self.engines: Dict[str, TTSEngine] = {
            'gtts': GTTSEngine(),
            # В будущем здесь можно добавить другие движки
            # 'piper': PiperTTSEngine(),
            # 'coqui': CoquiTTSEngine(),
        }
        
        # Маппинг языков на предпочтительные движки
        self.language_engine_map: Dict[str, str] = {
            # По умолчанию все языки используют Google TTS
            # В будущем для разных языков можно задать разные движки
        }
        
        logger.info(f"Сервис синтеза речи инициализирован с {len(self.engines)} движками")
        
    def _get_engine_for_language(self, language: str) -> TTSEngine:
        """Возвращает наиболее подходящий движок для указанного языка.
        
        Args:
            language: Код языка
            
        Returns:
            TTSEngine: Движок синтеза речи
        """
        # Проверяем, есть ли у нас специальный движок для этого языка
        preferred_engine_name = self.language_engine_map.get(language)
        
        if preferred_engine_name and preferred_engine_name in self.engines:
            engine = self.engines[preferred_engine_name]
            if engine.supports_language(language):
                return engine
        
        # Если нет специального движка или он не поддерживает язык,
        # перебираем все движки и выбираем первый подходящий
        for engine_name, engine in self.engines.items():
            if engine.supports_language(language):
                return engine
                
        # Если ни один движок не поддерживает язык, используем Google TTS с английским
        logger.warning(f"Ни один движок не поддерживает язык {language}, используем Google TTS с английским")
        return self.engines['gtts']
            
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
            lang = language if language and Config.is_language_supported(language) else Config.TARGET_LANGUAGE
            
            # Получаем подходящий движок
            engine = self._get_engine_for_language(lang)
            
            # Синтезируем речь
            return engine.synthesize(text, output_path, lang)
            
        except Exception as e:
            logger.error(f"Ошибка при синтезе речи: {e}", exc_info=True)
            return False
            
    def detect_audio_length(self, file_path: str) -> Optional[float]:
        """Определяет длительность аудиофайла в секундах.
        
        Args:
            file_path: Путь к аудиофайлу
            
        Returns:
            float: Длительность аудио в секундах или None в случае ошибки
        """
        try:
            # Используем ffprobe для получения информации о файле
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                   'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                   file_path]
                   
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            duration = float(result.stdout)
            
            return duration
            
        except Exception as e:
            logger.warning(f"Не удалось определить длительность аудио: {e}")
            return None 