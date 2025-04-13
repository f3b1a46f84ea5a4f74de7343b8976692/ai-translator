import logging
import tempfile
import os
import asyncio
import time
from telegram import Update, Voice, InputFile, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ChatAction

from src.services.transcription import TranscriptionService
from src.services.translation import TranslationService
from src.services.speech import SpeechService
from src.services.assistant import MistralAssistantService
from src.config import Config

logger = logging.getLogger(__name__)

# Префикс для callback данных
LANGUAGE_CALLBACK_PREFIX = "lang_"

class BotHandlers:
    def __init__(self):
        self.transcription_service = TranscriptionService()
        self.translation_service = TranslationService()
        self.speech_service = SpeechService()
        self.assistant_service = MistralAssistantService()

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
            
            lang_name = Config.get_language_name(lang_code)
            button = InlineKeyboardButton(
                text=lang_name.capitalize(),
                callback_data=f"{LANGUAGE_CALLBACK_PREFIX}{lang_code}"
            )
            row.append(button)
            
        if row:  # Добавляем последнюю строку, если она не пуста
            keyboard.append(row)
            
        # Добавляем кнопку "Другие языки"
        keyboard.append([
            InlineKeyboardButton(
                text="Другие языки/Other languages",
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
        
        for i, (lang_code, lang_name) in enumerate(Config.SUPPORTED_LANGUAGES.items()):
            if i > 0 and i % 2 == 0:  # Создаем новую строку каждые 2 кнопки
                keyboard.append(row)
                row = []
            
            button = InlineKeyboardButton(
                text=lang_name.capitalize(),
                callback_data=f"{LANGUAGE_CALLBACK_PREFIX}{lang_code}"
            )
            row.append(button)
            
        if row:  # Добавляем последнюю строку, если она не пуста
            keyboard.append(row)
            
        # Добавляем кнопку "Назад"
        keyboard.append([
            InlineKeyboardButton(
                text="← Назад/Back",
                callback_data=f"{LANGUAGE_CALLBACK_PREFIX}back"
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
            return ", ".join([f"{name} ({code})" for code, name in Config.SUPPORTED_LANGUAGES.items()])
        else:
            # Для других языков используем английские названия
            english_names = {
                'ar': 'Arabic', 'ja': 'Japanese', 'en': 'English', 'es': 'Spanish',
                'fr': 'French', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
                'zh': 'Chinese', 'ko': 'Korean', 'ru': 'Russian'
            }
            return ", ".join([f"{english_names.get(code, name)} ({code})" for code, name in Config.SUPPORTED_LANGUAGES.items()])

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
        
        # Сообщение о выбранном языке
        user_language = Config.get_user_language(user_id)
        
        if user_language == 'ru':
            message = f"Язык успешно изменен на {language_name}."
        else:
            english_names = {
                'ar': 'Arabic', 'ja': 'Japanese', 'en': 'English', 'es': 'Spanish',
                'fr': 'French', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
                'zh': 'Chinese', 'ko': 'Korean', 'ru': 'Russian'
            }
            language_name_en = english_names.get(lang_code, language_name)
            message = f"Language successfully changed to {language_name_en}."
        
        # Отвечаем пользователю
        await query.answer(message)
        
        # Обновляем сообщение с новой информацией
        languages = self._get_formatted_languages(lang_code)
        welcome_template = Config.WELCOME_MESSAGES.get(lang_code, Config.WELCOME_MESSAGES['en'])
        welcome_message = welcome_template.format(languages=languages)
        
        # Добавляем информацию о командах на выбранном языке
        if lang_code == 'ru':
            commands_info = "\n\nДоступные команды:\n/start - Начать работу с ботом\n/lang - Сменить язык"
            if self.assistant_service.is_available():
                commands_info += "\n/ask - Задать вопрос ИИ-ассистенту"
        else:
            commands_info = "\n\nAvailable commands:\n/start - Start working with the bot\n/lang - Change language"
            if self.assistant_service.is_available():
                commands_info += "\n/ask - Ask a question to the AI assistant"
                
        welcome_message += commands_info
        
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

    async def process_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        text = update.message.text

        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        source_lang = self.translation_service.detect_language(text)
        user_preferred_language = Config.get_user_language(user_id)
        
        if source_lang:
            if not Config.is_language_supported(source_lang):
                # Ответ на предпочитаемом языке пользователя
                if user_preferred_language == 'ru':
                    reply_text = f"Язык {Config.get_language_name(source_lang)} ({source_lang}) не поддерживается. Пожалуйста, используйте один из поддерживаемых языков."
                else:
                    reply_text = f"Language {source_lang} is not supported. Please use one of the supported languages."
                
                await update.message.reply_text(reply_text)
                return
                
            if source_lang != user_preferred_language:
                # Пробуем сначала перевести с Mistral API если он доступен
                if self.assistant_service.is_available():
                    translated_text = self.assistant_service.translate_with_context(
                        text=text, 
                        source_lang=source_lang, 
                        target_lang=user_preferred_language
                    )
                    
                    # Если по какой-то причине Mistral не справился, используем обычный перевод
                    if not translated_text:
                        translated_text = self.translation_service.translate(text, source_lang, user_preferred_language)
                else:
                    # Используем обычный перевод если Mistral недоступен
                    translated_text = self.translation_service.translate(text, source_lang, user_preferred_language)
            else:
                translated_text = text
        else:
            # Ответ на предпочитаемом языке пользователя
            if user_preferred_language == 'ru':
                reply_text = "Не удалось определить язык текста. Пожалуйста, попробуйте еще раз."
            else:
                reply_text = "Could not detect the language of the text. Please try again."
                
            await update.message.reply_text(reply_text)
            return

        if not translated_text:
            # Ответ на предпочитаемом языке пользователя
            if user_preferred_language == 'ru':
                reply_text = "Не удалось перевести текст."
            else:
                reply_text = "Failed to translate the text."
                
            await update.message.reply_text(reply_text)
            return

        # Ответ на предпочитаемом языке пользователя
        if user_preferred_language == 'ru':
            reply_text = f"Перевод:\n{translated_text}"
        else:
            reply_text = f"Translation:\n{translated_text}"
            
        await update.message.reply_text(reply_text)

        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.close()
            
            if self.speech_service.synthesize(translated_text, temp_file.name, language=user_preferred_language):
                with open(temp_file.name, 'rb') as audio_file:
                    # Ответ на предпочитаемом языке пользователя
                    if user_preferred_language == 'ru':
                        caption = "Озвученный перевод"
                    else:
                        caption = "Audio translation"
                        
                    await context.bot.send_voice(
                        chat_id=chat_id,
                        voice=InputFile(audio_file),
                        caption=caption
                    )
        finally:
            if temp_file and os.path.exists(temp_file.name):
                try:
                    await asyncio.sleep(1)
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный файл {temp_file.name}: {e}")

    async def process_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        voice = update.message.voice
        user_preferred_language = Config.get_user_language(user_id)

        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VOICE)
        
        voice_file = None
        temp_audio = None
        try:
            voice_file = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
            voice_file_path = voice_file.name
            voice_file.close()
            
            tg_file = await context.bot.get_file(voice.file_id)
            await tg_file.download_to_drive(voice_file_path)
            
            # Передаем предпочитаемый язык пользователя для лучшего распознавания
            transcribed_text = self.transcription_service.transcribe(voice_file_path, language=user_preferred_language)
            
            if not transcribed_text:
                # Ответ на предпочитаемом языке пользователя
                if user_preferred_language == 'ru':
                    reply_text = "Не удалось распознать речь."
                else:
                    reply_text = "Failed to recognize speech."
                
                await update.message.reply_text(reply_text)
                return

            # Ответ на предпочитаемом языке пользователя
            if user_preferred_language == 'ru':
                reply_text = f"Распознанный текст:\n{transcribed_text}"
            else:
                reply_text = f"Transcribed text:\n{transcribed_text}"
                
            await update.message.reply_text(reply_text)
            
            source_lang = self.translation_service.detect_language(transcribed_text)
            if source_lang:
                if not Config.is_language_supported(source_lang):
                    # Ответ на предпочитаемом языке пользователя
                    if user_preferred_language == 'ru':
                        reply_text = f"Язык {Config.get_language_name(source_lang)} ({source_lang}) не поддерживается. Пожалуйста, используйте один из поддерживаемых языков."
                    else:
                        reply_text = f"Language {source_lang} is not supported. Please use one of the supported languages."
                    
                    await update.message.reply_text(reply_text)
                    return
                    
                if source_lang != user_preferred_language:
                    # Пробуем сначала перевести с Mistral API если он доступен
                    if self.assistant_service.is_available():
                        translated_text = self.assistant_service.translate_with_context(
                            text=transcribed_text, 
                            source_lang=source_lang, 
                            target_lang=user_preferred_language
                        )
                        
                        # Если по какой-то причине Mistral не справился, используем обычный перевод
                        if not translated_text:
                            translated_text = self.translation_service.translate(transcribed_text, source_lang, user_preferred_language)
                    else:
                        # Используем обычный перевод если Mistral недоступен
                        translated_text = self.translation_service.translate(transcribed_text, source_lang, user_preferred_language)
                else:
                    translated_text = transcribed_text
            else:
                # Ответ на предпочитаемом языке пользователя
                if user_preferred_language == 'ru':
                    reply_text = "Не удалось определить язык распознанного текста. Пожалуйста, попробуйте еще раз."
                else:
                    reply_text = "Could not detect the language of the transcribed text. Please try again."
                    
                await update.message.reply_text(reply_text)
                return

            if not translated_text:
                # Ответ на предпочитаемом языке пользователя
                if user_preferred_language == 'ru':
                    reply_text = "Не удалось перевести текст."
                else:
                    reply_text = "Failed to translate the text."
                    
                await update.message.reply_text(reply_text)
                return

            # Ответ на предпочитаемом языке пользователя
            if user_preferred_language == 'ru':
                reply_text = f"Перевод:\n{translated_text}"
            else:
                reply_text = f"Translation:\n{translated_text}"
                
            await update.message.reply_text(reply_text)

            temp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_audio.close()
            
            if self.speech_service.synthesize(translated_text, temp_audio.name, language=user_preferred_language):
                with open(temp_audio.name, 'rb') as audio_file:
                    # Ответ на предпочитаемом языке пользователя
                    if user_preferred_language == 'ru':
                        caption = "Озвученный перевод"
                    else:
                        caption = "Audio translation"
                        
                    await context.bot.send_voice(
                        chat_id=chat_id,
                        voice=InputFile(audio_file),
                        caption=caption
                    )
        finally:
            for file_path in [voice_file_path if voice_file else None, 
                            temp_audio.name if temp_audio else None]:
                if file_path and os.path.exists(file_path):
                    try:
                        await asyncio.sleep(1)
                        os.unlink(file_path)
                    except Exception as e:
                        logger.warning(f"Не удалось удалить временный файл {file_path}: {e}")

    def get_handlers(self):
        return [
            CommandHandler('start', self.start),
            CommandHandler('lang', self.lang_command),
            CommandHandler('ask', self.ask_command),
            CallbackQueryHandler(self.language_callback, pattern=f"^{LANGUAGE_CALLBACK_PREFIX}"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_text),
            MessageHandler(filters.VOICE, self.process_voice)
        ] 