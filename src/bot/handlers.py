import logging
import tempfile
import os
import asyncio
import time
from telegram import Update, Voice, InputFile
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ChatAction

from src.services.transcription import TranscriptionService
from src.services.translation import TranslationService
from src.services.speech import SpeechService
from src.config import Config

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self):
        self.transcription_service = TranscriptionService()
        self.translation_service = TranslationService()
        self.speech_service = SpeechService()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        supported_languages = ", ".join([f"{name} ({code})" for code, name in Config.SUPPORTED_LANGUAGES.items()])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Привет! Я поддерживаю следующие языки:\n{supported_languages}\n\n"
                 "Отправь мне текстовое или голосовое сообщение на любом из этих языков, "
                 "и я переведу его на русский язык и озвучу."
        )

    async def process_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        text = update.message.text

        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        source_lang = self.translation_service.detect_language(text)
        if source_lang:
            if not Config.is_language_supported(source_lang):
                await update.message.reply_text(
                    f"Язык {Config.get_language_name(source_lang)} ({source_lang}) не поддерживается. "
                    "Пожалуйста, используйте один из поддерживаемых языков."
                )
                return
                
            if source_lang != Config.TARGET_LANGUAGE:
                translated_text = self.translation_service.translate(text, source_lang)
            else:
                translated_text = text
        else:
            await update.message.reply_text("Не удалось определить язык текста. Пожалуйста, попробуйте еще раз.")
            return

        if not translated_text:
            await update.message.reply_text("Не удалось перевести текст")
            return

        await update.message.reply_text(f"Перевод:\n{translated_text}")

        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.close()
            
            if self.speech_service.synthesize(translated_text, temp_file.name):
                with open(temp_file.name, 'rb') as audio_file:
                    await context.bot.send_voice(
                        chat_id=chat_id,
                        voice=InputFile(audio_file),
                        caption="Озвученный перевод"
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
        voice = update.message.voice

        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VOICE)
        
        voice_file = None
        temp_audio = None
        try:
            voice_file = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
            voice_file_path = voice_file.name
            voice_file.close()
            
            tg_file = await context.bot.get_file(voice.file_id)
            await tg_file.download_to_drive(voice_file_path)
            
            transcribed_text = self.transcription_service.transcribe(voice_file_path)
            
            if not transcribed_text:
                await update.message.reply_text("Не удалось распознать речь")
                return

            await update.message.reply_text(f"Распознанный текст:\n{transcribed_text}")
            
            source_lang = self.translation_service.detect_language(transcribed_text)
            if source_lang:
                if not Config.is_language_supported(source_lang):
                    await update.message.reply_text(
                        f"Язык {Config.get_language_name(source_lang)} ({source_lang}) не поддерживается. "
                        "Пожалуйста, используйте один из поддерживаемых языков."
                    )
                    return
                    
                if source_lang != Config.TARGET_LANGUAGE:
                    translated_text = self.translation_service.translate(transcribed_text, source_lang)
                else:
                    translated_text = transcribed_text
            else:
                await update.message.reply_text("Не удалось определить язык распознанного текста. Пожалуйста, попробуйте еще раз.")
                return

            if not translated_text:
                await update.message.reply_text("Не удалось перевести текст")
                return

            await update.message.reply_text(f"Перевод:\n{translated_text}")

            temp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_audio.close()
            
            if self.speech_service.synthesize(translated_text, temp_audio.name):
                with open(temp_audio.name, 'rb') as audio_file:
                    await context.bot.send_voice(
                        chat_id=chat_id,
                        voice=InputFile(audio_file),
                        caption="Озвученный перевод"
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
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_text),
            MessageHandler(filters.VOICE, self.process_voice)
        ] 