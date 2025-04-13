import logging
import tempfile
import os
import asyncio
import time
from telegram import Update, Voice, InputFile, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram.constants import ChatAction

from src.services.transcription import TranscriptionService
from src.services.translation import TranslationService
from src.services.speech import SpeechService
from src.services.assistant import MistralAssistantService
from src.services.llama_assistant import Llama31AssistantService
from src.config import Config
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# Префикс для callback данных
LANGUAGE_CALLBACK_PREFIX = "lang_"
TRANSLATE_CALLBACK_PREFIX = "trans_"
# Add the new prefix
ASSISTANT_CALLBACK_PREFIX = "asst_"

# Состояния для ConversationHandler
AWAITING_TRANSLATION_LANGUAGE = 1

class BotHandlers:
    def __init__(self):
        self.transcription_service = TranscriptionService()
        self.translation_service = TranslationService()
        self.speech_service = SpeechService()
        self.assistant_service = MistralAssistantService()
        self.tour_assistant_service = Llama31AssistantService()
        
        # Временное хранилище для данных перевода
        # {user_id: {"text": "...", "source_lang": "..."}}
        self.pending_translations = {}

    def _get_language_keyboard(self):
        """Создает клавиатуру для выбора языка.
        
        Returns:
            InlineKeyboardMarkup: Объект клавиатуры с кнопками выбора языка
        """
        keyboard = []
        row = []
        main_languages = ['en', 'ru', 'es', 'fr', 'de']
        
        for i, lang_code in enumerate(main_languages):
            if i > 0 and i % 3 == 0:  # Создаем новую строку каждые 3 кнопки
                keyboard.append(row)
                row = []
            
            # Получаем название языка на родном языке
            native_name = Config.get_native_language_name(lang_code)
            
            button = InlineKeyboardButton(
                text=native_name,
                callback_data=f"{LANGUAGE_CALLBACK_PREFIX}{lang_code}"
            )
            row.append(button)
            
        if row:  # Добавляем последнюю строку, если она не пуста
            keyboard.append(row)
            
        # Добавляем кнопку "Другие языки" на русском и английском
        keyboard.append([
            InlineKeyboardButton(
                text="🌐 Другие языки / Other languages",
                callback_data=f"{LANGUAGE_CALLBACK_PREFIX}more"
            )
        ])
            
        return InlineKeyboardMarkup(keyboard)
        
    def _get_all_languages_keyboard(self):
        """Создает клавиатуру для выбора из всех доступных языков.
        
        Returns:
            InlineKeyboardMarkup: Объект клавиатуры со всеми языками
        """
        keyboard = []
        row = []
        
        for i, lang_code in enumerate(Config.SUPPORTED_LANGUAGES.keys()):
            if i > 0 and i % 2 == 0:  # Создаем новую строку каждые 2 кнопки
                keyboard.append(row)
                row = []
            
            # Получаем название языка на родном языке
            native_name = Config.get_native_language_name(lang_code)
            
            button = InlineKeyboardButton(
                text=native_name,
                callback_data=f"{LANGUAGE_CALLBACK_PREFIX}{lang_code}"
            )
            row.append(button)
            
        if row:  # Добавляем последнюю строку, если она не пуста
            keyboard.append(row)
            
        # Добавляем кнопку "Назад" на русском и английском
        keyboard.append([
            InlineKeyboardButton(
                text="← Назад / Back",
                callback_data=f"{LANGUAGE_CALLBACK_PREFIX}back"
            )
        ])
            
        return InlineKeyboardMarkup(keyboard)

    def _get_translation_language_keyboard(self, exclude_lang=None):
        """Создает клавиатуру для выбора языка перевода.
        
        Args:
            exclude_lang: Язык, который нужно исключить из списка 
                          (обычно исходный язык сообщения)
                          
        Returns:
            InlineKeyboardMarkup: Объект клавиатуры с кнопками выбора языка
        """
        keyboard = []
        row = []
        
        # Отфильтровываем языки, исключая указанный язык
        languages = [lang for lang in Config.SUPPORTED_LANGUAGES.keys() 
                    if lang != exclude_lang]
        
        for i, lang_code in enumerate(languages):
            if i > 0 and i % 2 == 0:  # Создаем новую строку каждые 2 кнопки
                keyboard.append(row)
                row = []
            
            # Получаем название языка на родном языке
            native_name = Config.get_native_language_name(lang_code)
            
            button = InlineKeyboardButton(
                text=native_name,
                callback_data=f"{TRANSLATE_CALLBACK_PREFIX}{lang_code}"
            )
            row.append(button)
            
        if row:  # Добавляем последнюю строку, если она не пуста
            keyboard.append(row)
            
        # Добавляем кнопку "Спросить ассистента", если ассистент доступен
        if self.assistant_service.is_available():
            # Получаем язык пользователя для правильной надписи на кнопке
            user_id = self.pending_translations.get("user_id", 0)
            user_language = Config.get_user_language(user_id)
            
            button_text = "🤖 Спросить ассистента" if user_language == 'ru' else "🤖 Ask assistant"
            source_lang = self.pending_translations.get("original_lang" if "original_lang" in self.pending_translations else "source_lang", "en")
            
            keyboard.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"{ASSISTANT_CALLBACK_PREFIX}{source_lang}"
                )
            ])
            
        return InlineKeyboardMarkup(keyboard)
        
    def _get_formatted_languages(self, lang_code):
        """Форматирует список языков на заданном языке.
        
        Args:
            lang_code: Код языка для отображения
            
        Returns:
            str: Отформатированный список языков
        """
        if lang_code == 'ru':
            return ", ".join([f"{name} ({Config.get_native_language_name(code)})" 
                            for code, name in Config.SUPPORTED_LANGUAGES.items()])
        else:
            # Для других языков используем английские названия и родные названия
            english_names = {
                'ar': 'Arabic', 'ja': 'Japanese', 'en': 'English', 'es': 'Spanish',
                'fr': 'French', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
                'zh': 'Chinese', 'ko': 'Korean', 'ru': 'Russian'
            }
            return ", ".join([f"{english_names.get(code, name)} ({Config.get_native_language_name(code)})" 
                            for code, name in Config.SUPPORTED_LANGUAGES.items()])

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        
        # Определяем предпочтительный язык пользователя
        user_language = 'ru'  # По умолчанию русский
        
        # Если у пользователя есть языковой код из Telegram
        if user.language_code:
            # Если это двухбуквенный код, используем его
            if len(user.language_code) == 2 and Config.is_language_supported(user.language_code):
                user_language = user.language_code
            # Иначе берем первые две буквы (например, en-US -> en)
            elif len(user.language_code) > 2 and Config.is_language_supported(user.language_code[:2]):
                user_language = user.language_code[:2]
                
        # Сохраняем предпочтительный язык пользователя
        Config.set_user_language(user_id, user_language)
        
        # Форматируем список языков
        languages = self._get_formatted_languages(user_language)
        
        # Получаем приветственное сообщение на языке пользователя
        welcome_template = Config.WELCOME_MESSAGES.get(user_language, Config.WELCOME_MESSAGES['en'])
        welcome_message = welcome_template.format(languages=languages)
        
        # Добавляем информацию о командах
        if user_language == 'ru':
            commands_info = "\n\nДоступные команды:\n/start - Начать работу с ботом\n/lang - Сменить язык"
            if self.assistant_service.is_available():
                commands_info += "\n/ask - Задать вопрос ИИ-ассистенту"
        else:
            commands_info = "\n\nAvailable commands:\n/start - Start working with the bot\n/lang - Change language"
            if self.assistant_service.is_available():
                commands_info += "\n/ask - Ask a question to the AI assistant"
                
        welcome_message += commands_info
        
        # Отправляем сообщение с клавиатурой для выбора языка
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_message,
            reply_markup=self._get_language_keyboard()
        )
        
    async def lang_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /lang для смены языка.
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст для доступа к боту
        """
        user_id = update.effective_user.id
        user_language = Config.get_user_language(user_id)
        
        # Готовим сообщение на языке пользователя
        if user_language == 'ru':
            message = "Выберите предпочитаемый язык:"
        else:
            message = "Choose your preferred language:"
            
        # Отправляем сообщение с клавиатурой выбора языка
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_markup=self._get_language_keyboard()
        )

    async def language_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик колбэков от кнопок выбора языка.
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст для доступа к боту
        """
        query = update.callback_query
        user_id = query.from_user.id
        
        # Получаем выбранный язык из callback_data
        callback_data = query.data
        lang_code = callback_data[len(LANGUAGE_CALLBACK_PREFIX):]
        
        if lang_code == 'more':
            # Показываем клавиатуру со всеми языками
            await query.edit_message_reply_markup(
                reply_markup=self._get_all_languages_keyboard()
            )
            await query.answer()
            return
            
        if lang_code == 'back':
            # Возвращаемся к основной клавиатуре
            await query.edit_message_reply_markup(
                reply_markup=self._get_language_keyboard()
            )
            await query.answer()
            return
            
        # Сохраняем выбранный язык пользователя
        Config.set_user_language(user_id, lang_code)
        
        # Получаем имя языка
        language_name = Config.get_language_name(lang_code)
        native_name = Config.get_native_language_name(lang_code)
        
        # Сообщение о выбранном языке
        user_language = Config.get_user_language(user_id)
        
        if user_language == 'ru':
            message = f"Язык успешно изменен на {language_name} ({native_name})."
        else:
            english_names = {
                'ar': 'Arabic', 'ja': 'Japanese', 'en': 'English', 'es': 'Spanish',
                'fr': 'French', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
                'zh': 'Chinese', 'ko': 'Korean', 'ru': 'Russian'
            }
            language_name_en = english_names.get(lang_code, language_name)
            message = f"Language successfully changed to {language_name_en} ({native_name})."
        
        # Отвечаем пользователю
        await query.answer(message)
        
        # Обновляем сообщение с новой информацией
        languages = self._get_formatted_languages(lang_code)
        welcome_template = Config.WELCOME_MESSAGES.get(lang_code, Config.WELCOME_MESSAGES['en'])
        welcome_message = welcome_template.format(languages=languages)
        
        await query.edit_message_text(
            text=welcome_message,
            reply_markup=self._get_language_keyboard()
        )
        
    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /ask для взаимодействия с ИИ-ассистентом.
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст для доступа к боту
        """
        user_id = update.effective_user.id
        user_language = Config.get_user_language(user_id)
        
        # Проверяем, доступен ли сервис ассистента
        if not self.assistant_service.is_available():
            # Отвечаем на языке пользователя
            if user_language == 'ru':
                message = "Извините, сервис ИИ-ассистента в настоящее время недоступен. Проверьте настройки API ключа."
            else:
                message = "Sorry, the AI assistant service is currently unavailable. Please check the API key settings."
                
            await update.message.reply_text(message)
            return
            
        # Извлекаем вопрос из аргументов команды
        if not context.args or not ''.join(context.args).strip():
            # Отвечаем на языке пользователя
            if user_language == 'ru':
                message = "Пожалуйста, укажите ваш вопрос после команды /ask. Например: /ask Как работает переводчик?"
            else:
                message = "Please provide your question after the /ask command. For example: /ask How does the translator work?"
                
            await update.message.reply_text(message)
            return
            
        # Соединяем аргументы в один вопрос
        question = ' '.join(context.args)
        
        # Отправляем уведомление о печати
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        
        # Генерируем творческий ответ от ассистента
        response = self.assistant_service.generate_creative_response(
            prompt=question,
            language=user_language,
            creative_level=0.7
        )
        
        if not response:
            # Отвечаем на языке пользователя если что-то пошло не так
            if user_language == 'ru':
                message = "Извините, не удалось получить ответ от ассистента. Пожалуйста, попробуйте позже."
            else:
                message = "Sorry, could not get a response from the assistant. Please try again later."
                
            await update.message.reply_text(message)
            return
            
        # Отправляем ответ
        await update.message.reply_text(response)

    async def tour_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /tour для получения информации о турах по Краснодарскому краю.
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст для доступа к боту
        """
        user_id = update.effective_user.id
        user_language = Config.get_user_language(user_id)
        
        # Проверяем, доступен ли сервис ассистента туров
        if not self.tour_assistant_service.is_available():
            # Отвечаем на языке пользователя
            if user_language == 'ru':
                message = "Извините, сервис туристического ассистента в настоящее время недоступен. Проверьте настройки API ключа Llama."
            else:
                message = "Sorry, the tour assistant service is currently unavailable. Please check the Llama API key settings."
                
            await update.message.reply_text(message)
            return
            
        # Извлекаем запрос из аргументов команды
        if not context.args or not ''.join(context.args).strip():
            # Отвечаем на языке пользователя с примерами запросов
            if user_language == 'ru':
                message = "Пожалуйста, укажите ваш запрос о турах по Краснодарскому краю после команды /tour.\n\n" \
                          "Например:\n" \
                          "/tour Что посмотреть в Сочи?\n" \
                          "/tour Куда поехать с детьми в Геленджике?\n" \
                          "/tour Лучшее время для поездки в Краснодарский край\n" \
                          "/tour Винные туры в Абрау-Дюрсо"
            else:
                message = "Please provide your question about tours in the Krasnodar region after the /tour command.\n\n" \
                          "For example:\n" \
                          "/tour What to see in Sochi?\n" \
                          "/tour Where to go with children in Gelendzhik?\n" \
                          "/tour Best time to visit Krasnodar region\n" \
                          "/tour Wine tours in Abrau-Durso"
                
            await update.message.reply_text(message)
            return
            
        # Соединяем аргументы в один запрос
        query = ' '.join(context.args)
        
        # Отправляем уведомление о печати
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        
        # Получаем рекомендацию по турам от ассистента
        response = self.tour_assistant_service.get_tour_recommendation(
            query=query,
            language=user_language,
            temperature=0.7
        )
        
        if not response:
            # Отвечаем на языке пользователя если что-то пошло не так
            if user_language == 'ru':
                message = "Извините, не удалось получить информацию о турах. Пожалуйста, попробуйте позже или измените запрос."
            else:
                message = "Sorry, could not get information about tours. Please try again later or modify your query."
                
            await update.message.reply_text(message)
            return
            
        # Отправляем ответ
        await update.message.reply_text(response)

    async def process_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        text = update.message.text

        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        source_lang = self.translation_service.detect_language(text)
        user_preferred_language = Config.get_user_language(user_id)
        
        if not source_lang:
            # Ответ на предпочитаемом языке пользователя
            if user_preferred_language == 'ru':
                reply_text = "Не удалось определить язык текста. Пожалуйста, попробуйте еще раз."
            else:
                reply_text = "Could not detect the language of the text. Please try again."
                
            await update.message.reply_text(reply_text)
            return ConversationHandler.END
            
        if not Config.is_language_supported(source_lang):
            # Ответ на предпочитаемом языке пользователя
            if user_preferred_language == 'ru':
                reply_text = f"Язык {Config.get_language_name(source_lang)} ({source_lang}) не поддерживается. Пожалуйста, используйте один из поддерживаемых языков."
            else:
                reply_text = f"Language {source_lang} is not supported. Please use one of the supported languages."
            
            await update.message.reply_text(reply_text)
            return ConversationHandler.END
            
        # Если исходный язык уже английский, не делаем промежуточный перевод
        if source_lang == 'en':
            # Сохраняем информацию о тексте для последующего перевода
            self.pending_translations[user_id] = {
                "text": text,
                "source_lang": source_lang
            }
        else:
            # Сначала переводим на английский язык
            english_translation = self.translation_service.translate(text, source_lang=source_lang, target_lang='en')
            
            if not english_translation:
                # Перевод на английский не удался
                if user_preferred_language == 'ru':
                    reply_text = "Не удалось перевести текст на английский язык."
                else:
                    reply_text = "Failed to translate the text to English."
                    
                await update.message.reply_text(reply_text)
                return ConversationHandler.END
                
            # Сохраняем английский перевод для последующего перевода на другие языки
            self.pending_translations[user_id] = {
                "text": english_translation,
                "source_lang": 'en',
                "original_text": text,
                "original_lang": source_lang
            }
            
            # Если исходный язык отличается от английского, показываем исходный текст и английский перевод
            translation_header_en = Config.TRANSLATION_HEADERS.get('en', Config.TRANSLATION_HEADERS['en'])
            await update.message.reply_text(f"{translation_header_en}\n{english_translation}")
            
        # Получаем название исходного языка на языке пользователя
        if user_preferred_language == 'ru':
            source_lang_name = Config.get_language_name(source_lang)
        else:
            english_names = {
                'ar': 'Arabic', 'ja': 'Japanese', 'en': 'English', 'es': 'Spanish',
                'fr': 'French', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
                'zh': 'Chinese', 'ko': 'Korean', 'ru': 'Russian'
            }
            source_lang_name = english_names.get(source_lang, source_lang)
        
        # Запрашиваем у пользователя язык для прослушивания (не для перевода, т.к. мы уже сделали перевод)
        confirm_message = Config.TRANSLATION_CONFIRM_MESSAGES.get(
            user_preferred_language, 
            Config.TRANSLATION_CONFIRM_MESSAGES['en']
        ).format(source_lang=source_lang_name)
        
        # Отправляем сообщение с клавиатурой выбора языка
        await context.bot.send_message(
            chat_id=chat_id,
            text=confirm_message,
            reply_markup=self._get_translation_language_keyboard(exclude_lang=source_lang)
        )
        
        return AWAITING_TRANSLATION_LANGUAGE

    async def translation_language_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора языка для перевода.
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст для доступа к боту
        """
        query = update.callback_query
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        
        # Отвечаем на коллбэк, чтобы убрать "часики" у кнопки
        await query.answer()
        
        # Получаем выбранный язык перевода
        callback_data = query.data
        target_lang = callback_data[len(TRANSLATE_CALLBACK_PREFIX):]
        
        # Проверяем, есть ли данные для перевода
        if user_id not in self.pending_translations:
            # Отмечаем сообщение с выбором языка как изменённое и завершаем диалог
            user_preferred_language = Config.get_user_language(user_id)
            if user_preferred_language == 'ru':
                await query.edit_message_text("Данные для перевода устарели. Пожалуйста, отправьте текст снова.")
            else:
                await query.edit_message_text("Translation data expired. Please send your text again.")
                
            return ConversationHandler.END
            
        # Получаем данные для перевода
        translation_data = self.pending_translations[user_id]
        text = translation_data["text"]
        source_lang = translation_data["source_lang"]
        
        # Проверяем, если выбранный язык тот же, что и исходный
        if target_lang == source_lang:
            user_preferred_language = Config.get_user_language(user_id)
            if user_preferred_language == 'ru':
                await query.edit_message_text("Выбранный язык совпадает с исходным. Пожалуйста, выберите другой язык.")
            else:
                await query.edit_message_text("Selected language is the same as the source. Please choose a different language.")
                
            return ConversationHandler.END
            
        # Сообщаем пользователю, что начинаем перевод
        user_preferred_language = Config.get_user_language(user_id)
        translating_message = Config.TRANSLATING_MESSAGES.get(
            user_preferred_language, 
            Config.TRANSLATING_MESSAGES['en']
        ).format(target_lang=Config.get_language_name(target_lang))
        
        await query.edit_message_text(translating_message)
        
        # Отправляем индикатор набора текста
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # Переводим текст на выбранный язык
        # Мы уже имеем текст на английском (source_lang='en'), поэтому переводим с английского
        translated_text = self.translation_service.translate(text, source_lang='en', target_lang=target_lang)
        
        # Попробуем перевести с помощью Mistral, если стандартный перевод не удался
        if not translated_text and self.assistant_service.is_available():
            translated_text = self.assistant_service.translate_with_context(text, 'en', target_lang)
            
        # Удаляем данные из временного хранилища
        del self.pending_translations[user_id]
        
        if not translated_text:
            # Ответ на предпочитаемом языке пользователя
            if user_preferred_language == 'ru':
                reply_text = "Не удалось перевести текст."
            else:
                reply_text = "Failed to translate the text."
                
            await context.bot.send_message(chat_id=chat_id, text=reply_text)
            return ConversationHandler.END

        # Подготавливаем ответ на языке, выбранном пользователем для перевода
        translation_header = Config.TRANSLATION_HEADERS.get(target_lang, Config.TRANSLATION_HEADERS['en'])
        reply_text = f"{translation_header}\n{translated_text}"
            
        await context.bot.send_message(chat_id=chat_id, text=reply_text)

        # Запускаем генерацию аудио
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
        
        # Генерируем аудио перевода с использованием нашего модифицированного SpeechService
        temp_file = None
        try:
            # Создаем временный файл для аудио
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.close()
            
            # Синтезируем речь с использованием выбранного языка
            success = self.speech_service.synthesize(
                text=translated_text, 
                output_path=temp_file.name, 
                language=target_lang
            )
            
            if success:
                # Определяем длительность аудио
                audio_duration = self.speech_service.detect_audio_length(temp_file.name)
                duration_str = f" ({int(audio_duration)} сек)" if audio_duration else ""
                
                # Получаем подпись для аудио на выбранном языке
                audio_caption = Config.AUDIO_CAPTIONS.get(target_lang, Config.AUDIO_CAPTIONS['en'])
                
                # Отправляем аудиофайл
                with open(temp_file.name, 'rb') as audio_file:
                    await context.bot.send_audio(
                        chat_id=chat_id,
                        audio=audio_file,
                        caption=f"{audio_caption}{duration_str}",
                        title=f"Translation {source_lang} → {target_lang}"
                    )
            else:
                # Сообщаем об ошибке генерации аудио
                if user_preferred_language == 'ru':
                    error_message = "Не удалось создать аудио. Попробуйте позже."
                else:
                    error_message = "Failed to generate audio. Please try again later."
                    
                await context.bot.send_message(chat_id=chat_id, text=error_message)
                
        except Exception as e:
            logger.error(f"Ошибка при обработке аудио: {e}", exc_info=True)
            
            # Сообщаем об ошибке
            if user_preferred_language == 'ru':
                error_message = "Произошла ошибка при обработке аудио."
            else:
                error_message = "An error occurred while processing audio."
                
            await context.bot.send_message(chat_id=chat_id, text=error_message)
            
        finally:
            # Очищаем временный файл
            if temp_file:
                try:
                    import os
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный файл: {e}")
        
        return ConversationHandler.END

    async def process_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        voice = update.message.voice
        
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # Информируем пользователя о начале обработки
        user_preferred_language = Config.get_user_language(user_id)
        if user_preferred_language == 'ru':
            processing_message = "Обрабатываю голосовое сообщение..."
        else:
            processing_message = "Processing voice message..."
            
        processing_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=processing_message
        )
        
        # Скачиваем голосовое сообщение
        voice_file = await context.bot.get_file(voice.file_id)
        
        # Создаем временный файл для скачивания голосового сообщения
        import tempfile
        voice_temp = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
        voice_temp.close()
        
        try:
            # Показываем индикатор обработки записи
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
            
            # Скачиваем файл голосового сообщения
            await voice_file.download_to_drive(voice_temp.name)
            
            # Транскрибируем голосовое сообщение
            transcription_result = self.transcription_service.transcribe(voice_temp.name)
            
            # Обрабатываем результат транскрибации
            transcribed_text = None
            whisper_detected_language = None
            
            # Проверяем, что вернулось от метода транскрибации
            if isinstance(transcription_result, tuple) and len(transcription_result) == 2:
                # Если вернулся кортеж (текст, язык)
                transcribed_text, whisper_detected_language = transcription_result
            elif transcription_result:
                # Если вернулся только текст
                transcribed_text = transcription_result
            
            if not transcribed_text:
                # Если не удалось распознать речь
                if user_preferred_language == 'ru':
                    error_message = "Не удалось распознать речь. Пожалуйста, говорите чётче или используйте текстовое сообщение."
                else:
                    error_message = "Failed to recognize speech. Please speak more clearly or use a text message."
                    
                await processing_msg.edit_text(error_message)
                return
                
            # Показываем пользователю распознанный текст
            transcription_msg = f"🎤 {transcribed_text}"
            await processing_msg.edit_text(transcription_msg)
            
            # Логируем информацию о языке, если она есть
            if whisper_detected_language:
                logger.info(f"Whisper определил язык: {whisper_detected_language}")
                
            # Определяем язык распознанного текста, передавая определенный Whisper язык как подсказку
            source_lang = self.translation_service.detect_language(
                transcribed_text, 
                hint_language=whisper_detected_language
            )
            
            if not source_lang:
                # Если не удалось определить язык
                if user_preferred_language == 'ru':
                    error_message = "Не удалось определить язык речи. Пожалуйста, говорите чётче или используйте текстовое сообщение."
                else:
                    error_message = "Failed to detect speech language. Please speak more clearly or use a text message."
                    
                await context.bot.send_message(chat_id=chat_id, text=error_message)
                return ConversationHandler.END
                
            # Если исходный язык уже английский, не делаем промежуточный перевод
            if source_lang == 'en':
                # Сохраняем информацию о тексте для последующего перевода
                self.pending_translations[user_id] = {
                    "text": transcribed_text,
                    "source_lang": source_lang,
                    "user_id": user_id  # Сохраняем user_id для использования в клавиатуре
                }
            else:
                # Сначала переводим на английский язык
                english_translation = self.translation_service.translate(transcribed_text, source_lang=source_lang, target_lang='en')
                
                if not english_translation:
                    # Перевод на английский не удался
                    if user_preferred_language == 'ru':
                        reply_text = "Не удалось перевести речь на английский язык."
                    else:
                        reply_text = "Failed to translate speech to English."
                        
                    await context.bot.send_message(chat_id=chat_id, text=reply_text)
                    return ConversationHandler.END
                    
                # Сохраняем английский перевод для последующего перевода на другие языки
                self.pending_translations[user_id] = {
                    "text": english_translation,
                    "source_lang": 'en',
                    "original_text": transcribed_text,
                    "original_lang": source_lang,
                    "user_id": user_id  # Сохраняем user_id для использования в клавиатуре
                }
                
                # Если исходный язык отличается от английского, показываем английский перевод
                translation_header_en = Config.TRANSLATION_HEADERS.get('en', Config.TRANSLATION_HEADERS['en'])
                await context.bot.send_message(chat_id=chat_id, text=f"{translation_header_en}\n{english_translation}")
                
            # Получаем название исходного языка на языке пользователя
            if user_preferred_language == 'ru':
                source_lang_name = Config.get_language_name(source_lang)
            else:
                english_names = {
                    'ar': 'Arabic', 'ja': 'Japanese', 'en': 'English', 'es': 'Spanish',
                    'fr': 'French', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
                    'zh': 'Chinese', 'ko': 'Korean', 'ru': 'Russian'
                }
                source_lang_name = english_names.get(source_lang, source_lang)
            
            # Запрашиваем у пользователя язык для прослушивания
            confirm_message = Config.TRANSLATION_CONFIRM_MESSAGES.get(
                user_preferred_language, 
                Config.TRANSLATION_CONFIRM_MESSAGES['en']
            ).format(source_lang=source_lang_name)
            
            # Отправляем сообщение с клавиатурой выбора языка перевода
            await context.bot.send_message(
                chat_id=chat_id,
                text=confirm_message,
                reply_markup=self._get_translation_language_keyboard(exclude_lang=source_lang)
            )
            
            return AWAITING_TRANSLATION_LANGUAGE
                
        except Exception as e:
            logger.error(f"Ошибка при обработке голосового сообщения: {e}", exc_info=True)
            
            # Сообщаем об ошибке
            if user_preferred_language == 'ru':
                error_message = "Произошла ошибка при обработке голосового сообщения."
            else:
                error_message = "An error occurred while processing voice message."
                
            await processing_msg.edit_text(error_message)
            return ConversationHandler.END
            
        finally:
            # Очищаем временный файл
            try:
                import os
                os.unlink(voice_temp.name)
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл: {e}")

    async def assistant_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик запроса к ассистенту после распознавания голосового сообщения.
        
        Args:
            update: Объект обновления от Telegram
            context: Контекст для доступа к боту
        """
        query = update.callback_query
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        
        # Отвечаем на коллбэк, чтобы убрать "часики" у кнопки
        await query.answer()
        
        # Получаем язык запроса из callback_data
        callback_data = query.data
        request_lang = callback_data[len(ASSISTANT_CALLBACK_PREFIX):]
        
        # Проверяем, есть ли данные для обработки
        if user_id not in self.pending_translations:
            # Отмечаем сообщение как изменённое и завершаем диалог
            user_preferred_language = Config.get_user_language(user_id)
            if user_preferred_language == 'ru':
                await query.edit_message_text("Данные для обработки устарели. Пожалуйста, отправьте голосовое сообщение снова.")
            else:
                await query.edit_message_text("Voice data expired. Please send your voice message again.")
                
            return ConversationHandler.END
            
        # Получаем данные из временного хранилища
        translation_data = self.pending_translations[user_id]
        
        # Определяем текст запроса и язык
        if "original_text" in translation_data and "original_lang" in translation_data:
            # Используем оригинальный текст и язык, если доступны
            text = translation_data["original_text"]
            lang = translation_data["original_lang"]
        else:
            # Иначе используем текст и язык из сохраненных данных
            text = translation_data["text"]
            lang = translation_data["source_lang"]
        
        # Сообщаем пользователю, что запрос обрабатывается
        user_preferred_language = Config.get_user_language(user_id)
        if user_preferred_language == 'ru':
            processing_message = "Ассистент обрабатывает запрос..."
        else:
            processing_message = "Assistant is processing your request..."
            
        await query.edit_message_text(processing_message)
        
        # Отправляем индикатор набора текста
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # Генерируем ответ от ассистента на языке запроса
        response = self.assistant_service.generate_creative_response(
            prompt=text,
            language=lang,
            creative_level=0.7
        )
        
        # Удаляем данные из временного хранилища
        del self.pending_translations[user_id]
        
        if not response:
            # Если не удалось получить ответ от ассистента
            if user_preferred_language == 'ru':
                error_message = "Не удалось получить ответ от ассистента. Пожалуйста, попробуйте позже."
            else:
                error_message = "Failed to get a response from the assistant. Please try again later."
                
            await context.bot.send_message(chat_id=chat_id, text=error_message)
            return ConversationHandler.END
            
        # Отправляем ответ ассистента
        await context.bot.send_message(chat_id=chat_id, text=response)
        
        return ConversationHandler.END

    def get_handlers(self):
        text_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_text)],
            states={
                AWAITING_TRANSLATION_LANGUAGE: [
                    CallbackQueryHandler(
                        self.translation_language_callback, 
                        pattern=f"^{TRANSLATE_CALLBACK_PREFIX}"
                    ),
                    # Добавляем обработчик для кнопки ассистента
                    CallbackQueryHandler(
                        self.assistant_callback,
                        pattern=f"^{ASSISTANT_CALLBACK_PREFIX}"
                    )
                ]
            },
            fallbacks=[],
            name="text_translation_conversation",
            persistent=False
        )
        
        voice_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.VOICE, self.process_voice)],
            states={
                AWAITING_TRANSLATION_LANGUAGE: [
                    CallbackQueryHandler(
                        self.translation_language_callback, 
                        pattern=f"^{TRANSLATE_CALLBACK_PREFIX}"
                    ),
                    # Добавляем обработчик для кнопки ассистента
                    CallbackQueryHandler(
                        self.assistant_callback,
                        pattern=f"^{ASSISTANT_CALLBACK_PREFIX}"
                    )
                ]
            },
            fallbacks=[],
            name="voice_translation_conversation",
            persistent=False
        )
        
        return [
            CommandHandler('start', self.start),
            CommandHandler('lang', self.lang_command),
            CommandHandler('ask', self.ask_command),
            CommandHandler('tour', self.tour_command),
            CallbackQueryHandler(self.language_callback, pattern=f"^{LANGUAGE_CALLBACK_PREFIX}"),
            text_handler,
            voice_handler
        ] 