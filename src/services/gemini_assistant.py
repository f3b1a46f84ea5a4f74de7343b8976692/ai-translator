import logging
import os
import requests
import json
from typing import Optional, Dict, List, Any, Union
from src.config import Config

logger = logging.getLogger(__name__)

class GeminiAssistantService:
    """Сервис для взаимодействия с Gemini 2.0 Flash API для генерации текста."""
    
    def __init__(self):
        """Инициализация сервиса Gemini API."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        
        if not self.is_available():
            logger.warning("Gemini API key не установлен. Функциональность ИИ-ассистента будет недоступна.")
        else:
            logger.info("Gemini API инициализирован")
        
    def is_available(self) -> bool:
        """Проверяет, доступен ли сервис Gemini API.
        
        Returns:
            bool: True, если API ключ настроен, иначе False
        """
        return self.api_key is not None and self.api_key != ""
        
    def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> Optional[str]:
        """Генерирует ответ с использованием Gemini API.
        
        Args:
            prompt: Запрос пользователя
            system_prompt: Системный промпт
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе
            
        Returns:
            str: Сгенерированный ответ или None в случае ошибки
        """
        if not self.is_available():
            logger.warning("Попытка использования Gemini API без настроенного ключа")
            return None
            
        try:
            # Формируем сообщения для API
            messages = []
            
            # Добавляем системный промпт, если он указан
            if system_prompt:
                messages.append({"role": "user", "parts": [{"text": system_prompt}]})
                
            # Добавляем текущий запрос пользователя
            messages.append({"role": "user", "parts": [{"text": prompt}]})
            
            # Формируем запрос к API
            headers = {
                "Content-Type": "application/json",
            }
            
            payload = {
                "contents": messages,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                }
            }
            
            # Выполняем запрос к API
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            # Проверяем успешность запроса
            response.raise_for_status()
            
            # Обрабатываем ответ
            response_data = response.json()
            
            # Извлекаем сгенерированный текст
            if "candidates" in response_data and len(response_data["candidates"]) > 0:
                return response_data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                logger.warning("Неожиданный формат ответа от Gemini API")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к Gemini API: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при декодировании ответа от Gemini API: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при работе с Gemini API: {e}")
            return None
            
    def translate_with_context(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        """Переводит текст с учетом контекста с помощью Gemini API.
        
        Использует контекстно-зависимый перевод, который может быть лучше
        для сложных текстов или идиом, чем обычный переводчик.
        
        Args:
            text: Текст для перевода
            source_lang: Исходный язык
            target_lang: Целевой язык
            
        Returns:
            str: Переведенный текст или None в случае ошибки
        """
        if not self.is_available():
            logger.debug("Перевод с использованием Gemini пропущен, API ключ не настроен")
            return None
            
        try:
            # Получаем названия языков
            source_lang_name = Config.get_language_name(source_lang)
            target_lang_name = Config.get_language_name(target_lang)
            
            # Формируем системный промпт для перевода
            system_prompt = f"""You are a professional translator. 
Your task is to translate text from {source_lang_name} ({source_lang}) to {target_lang_name} ({target_lang}).
Translate the text accurately while preserving the original meaning, tone, and style.
Respond ONLY with the translated text, without any explanations or comments."""

            # Формируем запрос к API
            response = self.generate_response(
                prompt=text,
                system_prompt=system_prompt,
                temperature=0.3,  # Низкая температура для более точного перевода
                max_tokens=1024   # Увеличиваем лимит токенов для длинных текстов
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка при переводе с использованием Gemini API: {e}")
            return None
            
    def generate_creative_response(
        self,
        prompt: str,
        language: str,
        creative_level: float = 0.7
    ) -> Optional[str]:
        """Генерирует творческий ответ на запрос пользователя.
        
        Args:
            prompt: Запрос пользователя
            language: Язык ответа
            creative_level: Уровень креативности (0.0-1.0)
            
        Returns:
            str: Сгенерированный ответ или None в случае ошибки
        """
        if not self.is_available():
            logger.debug("Генерация ответа с использованием Gemini пропущена, API ключ не настроен")
            return None
            
        try:
            # Получаем название языка
            language_name = Config.get_language_name(language)
            
            # Формируем системный промпт
            system_prompt = f"""You are a creative assistant that responds in {language_name}.
Generate a creative and engaging response to the user's prompt.
Your response should be insightful, helpful, and tailored to the user's request."""

            # Формируем запрос к API
            response = self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=creative_level,
                max_tokens=1024
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка при генерации творческого ответа: {e}")
            return None 