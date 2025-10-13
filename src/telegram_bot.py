#!/usr/bin/env python3
"""
Bot de Telegram para Saú AI - Asistente especializado en vida saludable
Integra el chatbot RAG con la API de Telegram
"""

import logging
import os
import asyncio
from datetime import datetime
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
#from dotenv import load_dotenv # Ya cargado en run_telegram_bot.py
from RAG_ChatBot import SauAI
from session_manager import SessionManager
from user_manager import UserManager
from bot_core import BotCore, MessageInput, MessageResponse
import uuid

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramSauAI:
    def __init__(self, user_manager: UserManager, session_manager: SessionManager):
        """Inicializa el bot de Telegram con BotCore"""
        #load_dotenv() # Ya cargado en run_telegram_bot.py
        
        # Token del bot de Telegram
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN no está configurado en .env")
        
        # Crear aplicación
        self.application = Application.builder().token(self.bot_token).build()
        
        # Asignar gestores de sesiones y usuarios
        self.session_manager = session_manager
        self.user_manager = user_manager
        
        # Inicializar BotCore (contiene toda la lógica de negocio)
        try:
            self.bot_core = BotCore(user_manager, session_manager)
            logger.info("✅ BotCore inicializado correctamente en TelegramSauAI")
        except Exception as e:
            logger.error(f"❌ Error al inicializar BotCore: {e}")
            raise
        
        # Configurar handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura los handlers del bot"""
        # Solo mensajes de texto, sin comandos
        self.application.add_handler(MessageHandler(filters.TEXT, self.handle_message))
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto del usuario de forma simple"""
        if not update.message or not update.message.text or not update.message.from_user:
            return
            
        # Procesar mensaje de forma asíncrona
        task = asyncio.create_task(self._process_message_async(update, context))
        
        # Agregar callback para manejar errores no capturados
        def handle_task_exception(task):
            if task.exception():
                logger.error(f"❌ Error no capturado en procesamiento asíncrono: {task.exception()}")
        
        task.add_done_callback(handle_task_exception)
    
    async def _process_message_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa un mensaje de forma asíncrona usando BotCore"""
        if not update.message or not update.message.text or not update.message.from_user:
            return
            
        user_id = update.message.from_user.id
        user_message = update.message.text
        
        try:
            # Registrar o actualizar usuario en la base de datos con reintentos
            user_info = await self._safe_user_operation(update.message.from_user)
            
            # Obtener username para la sesión
            username = update.message.from_user.username or f"user_{user_id}"
            
            # Mostrar que el bot está escribiendo
            await update.message.reply_chat_action("typing")
            
            # Crear entrada de mensaje genérica
            message_input = MessageInput(
                username=username,
                message=user_message,
                origin="telegram",
                metadata={
                    "telegram_user_id": user_id,
                    "first_name": update.message.from_user.first_name,
                    "last_name": update.message.from_user.last_name
                }
            )
            
            # Procesar mensaje usando BotCore (lógica central desacoplada)
            response = await self.bot_core.process_message(message_input)
            
            # Enviar respuesta adaptada a Telegram
            await self._send_response(update, response)
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            if update.message:
                await update.message.reply_text(
                    "❌ Lo siento, ocurrió un error al procesar tu pregunta. Por favor, intenta nuevamente."
                )
    
    async def _safe_user_operation(self, user_data):
        """Operación segura para crear/actualizar usuario con reintentos"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self.executor,
                    self.user_manager.create_or_update_user,
                    user_data
                )
            except Exception as e:
                logger.warning(f"⚠️ Intento {attempt + 1} fallido para operación de usuario: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)  # Esperar antes del siguiente intento

# Las funciones _safe_session_operation, _safe_add_message, _safe_process_with_sauai y _process_with_sauai
# han sido movidas a BotCore para centralizar la lógica de negocio
    
    async def _send_response(self, update: Update, response: MessageResponse):
        """Envía una respuesta adaptada a Telegram desde formato genérico"""
        if not update.message:
            return
        
        # Manejar diferentes tipos de respuesta
        if response.response_type == "text":
            content = response.content
            # Si la respuesta es muy larga, dividirla simplemente
            if len(content) > 4000:
                parts = [content[i:i+4000] for i in range(0, len(content), 4000)]
                for part in parts:
                    await update.message.reply_text(part)
            else:
                await update.message.reply_text(content)
        
        elif response.response_type == "typing":
            # Para typing, no enviamos nada ya que ya se envió antes
            pass
        
        elif response.response_type == "error":
            await update.message.reply_text(response.content)
        
        else:
            # Tipo desconocido, enviar como texto
            await update.message.reply_text(response.content)
    
    def run(self):
        """Ejecuta el bot"""
        logger.info("🚀 Iniciando bot de Telegram...")
        
        try:
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                poll_interval=2.0,
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Error ejecutando bot: {e}")
            raise
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpia recursos al cerrar el bot"""
        logger.info("🧹 Limpiando recursos de TelegramSauAI...")
        try:
            # Limpiar BotCore
            if hasattr(self, 'bot_core') and self.bot_core:
                self.bot_core.cleanup()
                logger.info("✅ BotCore limpiado correctamente")
        except Exception as e:
            logger.error(f"Error durante cleanup: {e}")

# La función main ha sido movida a run_telegram_bot.py
# def main():
#     """Función principal para ejecutar el bot"""
#     try:
#         bot = TelegramSauAI()
#         bot.run()
#     except KeyboardInterrupt:
#         logger.info("Bot detenido por el usuario")
#     except Exception as e:
#         logger.error(f"Error fatal: {e}")

# if __name__ == "__main__":
#     main()