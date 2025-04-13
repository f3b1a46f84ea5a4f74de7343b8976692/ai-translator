import logging
import os
import requests
import json
import time
from typing import Optional, Dict, List, Any, Union
from src.config import Config
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class Llama31AssistantService:
    """Сервис для взаимодействия с API Llama 3.1 для информации о турах по Краснодарскому краю."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        api_url: str = "https://api.perplexity.ai/chat/completions",
        model: str = "llama-3.1-8b-instant"
    ):
        """
        Инициализация сервиса Llama 3.1 для туров по Краснодарскому краю.
        
        Args:
            api_key: API ключ для Llama API. Если None, будет использован из переменной окружения.
            api_url: URL для запросов к Llama API.
            model: Название модели для использования.
        """
        self.api_key = api_key or os.getenv("LLAMA_API_KEY", "")
        self.api_url = api_url
        self.model = model
        
        # Проверяем доступность API ключа
        if not self.api_key:
            logger.warning("Llama API key is not set. Tour recommendations will not be available.")
        
        # Информация о доступных турах по Краснодарскому краю
        self.krasnodar_tours_data = {
            "Сочи": ["Красная Поляна", "Олимпийский парк", "Дендрарий", "Роза Хутор"],
            "Краснодар": ["Улица Красная", "Парк Галицкого", "Музей Фелицына"],
            "Геленджик": ["Набережная", "Сафари-парк", "Канатная дорога"],
            "Анапа": ["Большой Утриш", "Парк 30-летия Победы", "Песчаные пляжи"],
            "Новороссийск": ["Крейсер Михаил Кутузов", "Малая земля", "Набережная адмирала Серебрякова"],
            "Горячий Ключ": ["Дантово ущелье", "Минеральные источники", "Скала Петушок"],
            "Абрау-Дюрсо": ["Винзавод Абрау-Дюрсо", "Озеро Абрау", "Дегустации вина"]
        }
        
        # Информация о сезонах
        self.seasons_info = {
            "Лето": "Высокий сезон (июнь-август): идеально для пляжного отдыха, температура воды 23-27°C",
            "Весна": "Мягкий климат (апрель-май): цветение, меньше туристов, экскурсионные программы",
            "Осень": "Бархатный сезон (сентябрь-октябрь): теплое море, сбор винограда, меньше людей",
            "Зима": "Горнолыжный сезон в Красной Поляне (декабрь-март), новогодние праздники в Сочи"
        }
        
        if not self.is_available():
            logger.warning("Llama API key не установлен. Функциональность ИИ-ассистента по турам будет недоступна.")
        else:
            logger.info(f"Llama API инициализирован с моделью {self.model}")
        
    def is_available(self) -> bool:
        """Проверяет, доступен ли сервис Llama API.
        
        Returns:
            bool: True, если API ключ установлен, иначе False
        """
        return bool(self.api_key)
    
    def search_krasnodar_tours(self, query: str) -> Dict[str, List[str]]:
        """
        Поиск информации о турах и достопримечательностях в Краснодарском крае.
        
        Args:
            query: Поисковый запрос пользователя.
            
        Returns:
            Dict с результатами поиска по категориям.
        """
        query = query.lower()
        results = {
            "cities": [],
            "attractions": [],
            "seasons": []
        }
        
        # Поиск по городам
        for city in self.krasnodar_tours_data.keys():
            if city in query:
                results["cities"].append(city)
                
                # Добавляем достопримечательности для найденного города
                if "достопримечательност" in query or "посмотреть" in query or "посетить" in query:
                    results["attractions"].extend(self.krasnodar_tours_data[city])
                
                # Добавляем информацию для семей, если это запрашивается
                if "дети" in query or "семь" in query or "ребенок" in query or "детьми" in query:
                    results["attractions"].extend(self.krasnodar_tours_data[city])
                
                # Добавляем специфичную информацию для определенных городов
                if city == "абрау-дюрсо" and ("вино" in query or "винн" in query or "дегустац" in query):
                    results["attractions"].extend(self.krasnodar_tours_data[city])
                
                if city == "горячий ключ" and ("лечени" in query or "здоровь" in query or "санатор" in query):
                    results["attractions"].extend(self.krasnodar_tours_data[city])
        
        # Поиск по сезонам
        for season in self.seasons_info.keys():
            if season in query or self._is_season_related(query, season):
                results["seasons"].append(season)
                
        # Если не нашли конкретный город, но есть общие запросы
        if not results["cities"]:
            if "дети" in query or "семь" in query or "ребенок" in query or "детьми" in query:
                for city, info in self.krasnodar_tours_data.items():
                    if "дети" in query or "семь" in query or "ребенок" in query or "детьми" in query:
                        if city not in results["cities"]:
                            results["cities"].append(city)
                        results["attractions"].extend(info)
            
            if "вино" in query or "винн" in query or "дегустац" in query:
                if "абрау-дюрсо" not in results["cities"]:
                    results["cities"].append("абрау-дюрсо")
                results["attractions"].extend(self.krasnodar_tours_data["абрау-дюрсо"])
            
            if "лечени" in query or "здоровь" in query or "санатор" in query:
                if "горячий ключ" not in results["cities"]:
                    results["cities"].append("горячий ключ")
                results["attractions"].extend(self.krasnodar_tours_data["горячий ключ"])
                
        return results
    
    def _is_season_related(self, query: str, season: str) -> bool:
        """
        Проверяет, связан ли запрос с определенным сезоном.
        
        Args:
            query: Поисковый запрос пользователя.
            season: Сезон для проверки.
            
        Returns:
            bool: True, если запрос связан с сезоном.
        """
        if season == "лето":
            return any(word in query for word in ["июнь", "июль", "август", "жар", "пляж", "купани"])
        elif season == "осень":
            return any(word in query for word in ["сентябрь", "октябрь", "ноябрь", "бархатн"])
        elif season == "зима":
            return any(word in query for word in ["декабрь", "январь", "февраль", "лыж", "новый год", "рождеств"])
        elif season == "весна":
            return any(word in query for word in ["март", "апрель", "май", "цветени"])
        return False
    
    def generate_response(
        self, 
        user_prompt: str, 
        system_prompt: str = None,
        search_results: Optional[Dict[str, List[str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Optional[str]:
        """
        Генерация ответа с использованием Llama API.
        
        Args:
            user_prompt: Запрос пользователя.
            system_prompt: Системный промпт для задания контекста.
            search_results: Результаты поиска по базе знаний о Краснодарском крае.
            temperature: Температура для генерации (креативность ответа).
            max_tokens: Максимальное количество токенов в ответе.
            
        Returns:
            str: Сгенерированный ответ или None в случае ошибки.
        """
        if not self.is_available():
            logger.warning("Llama API is not available. Cannot generate response.")
            return None
        
        # Формируем системный промпт с дополнительной информацией о турах
        if not system_prompt:
            system_prompt = "Ты - туристический ассистент, специализирующийся на Краснодарском крае России. " \
                           "Твоя задача - предоставлять точную и полезную информацию о туристических местах, " \
                           "достопримечательностях, сезонах для посещения и интересных активностях в регионе. " \
                           "Давай краткие, но содержательные ответы, фокусируясь на конкретных запросах пользователя."
        
        # Добавляем результаты поиска к промпту, если они есть
        if search_results:
            system_prompt += "\n\nИнформация о запрашиваемом месте или сезоне:"
            
            if search_results.get("cities"):
                system_prompt += "\nНайденные города: " + ", ".join(search_results["cities"])
            
            if search_results.get("attractions"):
                system_prompt += "\nДостопримечательности и активности:"
                for attraction in search_results["attractions"]:
                    system_prompt += f"\n- {attraction}"
            
            if search_results.get("seasons"):
                system_prompt += "\nИнформация о сезонах:"
                for season in search_results["seasons"]:
                    system_prompt += f"\n- {season.capitalize()}:"
                    for highlight in self.seasons_info[season].split(", "):
                        system_prompt += f"\n  * {highlight}"
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            logger.debug(f"Sending request to Llama API: {self.api_url}")
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload)
            )
            
            if response.status_code != 200:
                logger.error(f"Error from Llama API: {response.status_code} - {response.text}")
                return None
            
            response_data = response.json()
            logger.debug(f"Received response from Llama API: {response_data}")
            
            if "choices" in response_data and response_data["choices"]:
                return response_data["choices"][0]["message"]["content"]
            
            logger.error(f"Unexpected response format from Llama API: {response_data}")
            return None
            
        except Exception as e:
            logger.error(f"Error while generating response with Llama API: {str(e)}")
            return None
    
    def get_tour_recommendation(
        self, 
        query: str, 
        language: str = "ru",
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Получение рекомендаций по турам в Краснодарском крае.
        
        Args:
            query: Запрос пользователя о турах.
            language: Язык ответа ('ru' для русского, иначе английский).
            temperature: Температура для генерации (креативность ответа).
            
        Returns:
            str: Рекомендация по турам или None в случае ошибки.
        """
        if not self.is_available():
            logger.warning("Llama API is not available. Cannot provide tour recommendation.")
            return None
        
        # Поиск по базе знаний
        search_results = self.search_krasnodar_tours(query.lower())
        
        # Формируем системный промпт в зависимости от языка
        if language == "ru":
            system_prompt = "Ты - туристический ассистент, специализирующийся на Краснодарском крае России. " \
                           "Твоя задача - предоставлять точную и полезную информацию о туристических местах, " \
                           "достопримечательностях, сезонах для посещения и интересных активностях в регионе. " \
                           "Давай краткие, но содержательные ответы на русском языке, фокусируясь на конкретных запросах пользователя."
        else:
            system_prompt = "You are a tour assistant specializing in the Krasnodar region of Russia. " \
                           "Your task is to provide accurate and useful information about tourist places, " \
                           "attractions, seasons to visit, and interesting activities in the region. " \
                           "Give concise but informative answers in English, focusing on the specific user requests."
        
        # Генерируем ответ
        return self.generate_response(
            user_prompt=query,
            system_prompt=system_prompt,
            search_results=search_results,
            temperature=temperature
        )
    
    def translate_with_context(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str,
        context: Optional[str] = None,
        temperature: float = 0.3
    ) -> Optional[str]:
        """
        Перевод текста с учетом контекста с помощью Llama API.
        
        Args:
            text: Текст для перевода.
            source_lang: Исходный язык текста.
            target_lang: Целевой язык перевода.
            context: Контекст для улучшения качества перевода.
            temperature: Температура для генерации (точность перевода).
            
        Returns:
            str: Переведенный текст или None в случае ошибки.
        """
        if not self.is_available():
            logger.warning("Llama API is not available. Cannot perform translation.")
            return None
        
        # Формируем промпт для перевода
        if context:
            user_prompt = f"Translate the following text from {source_lang} to {target_lang}. Context: {context}\n\nText to translate: {text}"
        else:
            user_prompt = f"Translate the following text from {source_lang} to {target_lang}: {text}"
        
        system_prompt = "You are a professional translator. Provide accurate translations while maintaining the original meaning, tone, and style. Do not add explanations or notes - just the translation."
        
        # Генерируем перевод
        return self.generate_response(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature
        ) 