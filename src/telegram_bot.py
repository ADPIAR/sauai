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
import uuid

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramSauAI:
    def __init__(self, user_manager: UserManager, session_manager: SessionManager):
        """Inicializa el bot de Telegram con SauAI"""
        #load_dotenv() # Ya cargado en run_telegram_bot.py
        
        # Inicializar SauAI
        try:
            self.sau_ai = SauAI()
            logger.info("✅ SauAI inicializado correctamente")
        except Exception as e:
            logger.error(f"❌ Error al inicializar SauAI: {e}")
            raise
        
        # Token del bot de Telegram
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN no está configurado en .env")
        
        # Crear aplicación
        self.application = Application.builder().token(self.bot_token).build()
        
        # Asignar gestores de sesiones y usuarios
        self.session_manager = session_manager
        self.user_manager = user_manager
        
        # Inicializar ThreadPoolExecutor para procesamiento concurrente
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="SauAI-")
        
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
        """Procesa un mensaje de forma asíncrona con manejo robusto de errores"""
        if not update.message or not update.message.text or not update.message.from_user:
            return
            
        user_id = update.message.from_user.id
        user_message = update.message.text
        
        try:
            # Registrar o actualizar usuario en la base de datos con reintentos
            user_info = await self._safe_user_operation(update.message.from_user)
            
            # Obtener username para la sesión
            username = update.message.from_user.username or f"user_{user_id}"
            
            # Obtener o crear sesión del usuario con reintentos
            user_session = await self._safe_session_operation(username)
            
            # Guardar mensaje del usuario en historial usando session_id
            await self._safe_add_message(user_session.session_id, user_message, is_user=True)
            
            # Mostrar que el bot está escribiendo
            await update.message.reply_chat_action("typing")
            
            # Procesar mensaje con SauAI con timeout y reintentos
            response = await self._safe_process_with_sauai(username, user_session.session_id, user_message)
            
            # Guardar respuesta en historial usando session_id
            await self._safe_add_message(user_session.session_id, response, is_user=False)
            
            # Enviar respuesta de forma simple
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

    async def _safe_session_operation(self, username: str):
        """Operación segura para obtener/crear sesión con reintentos"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self.executor,
                    self.session_manager.get_or_create_session,
                    username
                )
            except Exception as e:
                logger.warning(f"⚠️ Intento {attempt + 1} fallido para operación de sesión: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)  # Esperar antes del siguiente intento

    async def _safe_add_message(self, session_id: uuid.UUID, message: str, is_user: bool = True):
        """Operación segura para agregar mensaje con reintentos"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self.executor,
                    self.session_manager.add_message_to_history,
                    session_id,
                    message,
                    is_user
                )
                return
            except Exception as e:
                logger.warning(f"⚠️ Intento {attempt + 1} fallido para agregar mensaje: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)  # Esperar antes del siguiente intento

    async def _safe_process_with_sauai(self, username: str, session_id: uuid.UUID, user_message: str) -> str:
        """Procesa un mensaje con SauAI de forma segura con timeout y reintentos"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        self._process_with_sauai,
                        username,
                        session_id,
                        user_message
                    ),
                    timeout=60
                )
                return response
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Timeout en intento {attempt + 1} para usuario {username}")
                if attempt == max_retries - 1:
                    return "❌ Lo siento, el procesamiento está tomando demasiado tiempo. Por favor, intenta con una pregunta más simple."
            except Exception as e:
                logger.warning(f"⚠️ Error en intento {attempt + 1} para usuario {username}: {e}")
                if attempt == max_retries - 1:
                    return "❌ Lo siento, ocurrió un error al procesar tu pregunta. Por favor, intenta nuevamente."
                await asyncio.sleep(2)  # Esperar antes del siguiente intento

    def _process_with_sauai(self, username: str, session_id: uuid.UUID, user_message: str) -> str:
        """Procesa un mensaje con SauAI - SIMPLIFICADO"""
        try:
            # Obtener información básica del usuario para contexto desde UserManager
            user_info = self.user_manager.get_user(username)
            
            # Crear contexto mínimo y natural
            context_parts = []
            
            if user_info and user_info.personal_name:
                context_parts.append(f"El usuario se llama {user_info.personal_name}")
            
            if user_info and user_info.age:
                context_parts.append(f"tiene {user_info.age} años")
            
            if user_info and user_info.user_needs:
                context_parts.append(f"sus objetivos son: {user_info.user_needs}")
            
            # Obtener contexto de conversación reciente usando session_id
            conversation_context = self.session_manager.get_conversation_context(session_id, limit=5)
            
            if context_parts or conversation_context:
                context_info = ". ".join(context_parts) if context_parts else ""
                full_context = f"{context_info}\n\nConversación reciente:\n{conversation_context}" if conversation_context else context_info
                enhanced_question = f"Contexto: {full_context}\n\nPregunta: {user_message}"
            else:
                enhanced_question = user_message
            
            # Procesar con SauAI
            response = self.sau_ai.ask(enhanced_question)
            return response
            
        except Exception as e:
            logger.error(f"❌ Error procesando con SauAI para usuario {username}: {e}")
            return "❌ Lo siento, ocurrió un error al procesar tu pregunta. Por favor, intenta nuevamente."
    
    async def _send_response(self, update: Update, response: str):
        """Envía una respuesta de forma simple"""
        if not update.message:
            return
        
        # Si la respuesta es muy larga, dividirla simplemente
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(response)
    
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
        logger.info("🧹 Limpiando recursos...")
        try:
            if hasattr(self, 'executor') and self.executor:
                self.executor.shutdown(wait=True, cancel_futures=True)
                logger.info("✅ ThreadPoolExecutor cerrado correctamente")
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