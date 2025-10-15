#!/usr/bin/env python3
"""
Bot Core - Lógica central desacoplada del bot SAÚ AI
Maneja el procesamiento de mensajes independientemente de la plataforma (Telegram, Web, etc.)
"""

import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from RAG_ChatBot import SauAI
from session_manager import SessionManager
from user_manager import UserManager, UserInfo

# Configurar logging
logger = logging.getLogger(__name__)

@dataclass
class MessageInput:
    """Formato genérico para entrada de mensajes desde cualquier plataforma"""
    username: str
    message: str
    origin: str  # "telegram", "web", etc.
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class MessageResponse:
    """Formato genérico para respuestas que pueden ser adaptadas a cualquier plataforma"""
    content: str
    response_type: str = "text"  # "text", "typing", "error"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BotCore:
    """
    Lógica central del bot SAÚ AI desacoplada de plataformas específicas
    """
    
    def __init__(self, user_manager: UserManager, session_manager: SessionManager):
        """Inicializa el core del bot con los managers existentes"""
        
        # Inicializar SauAI
        try:
            self.sau_ai = SauAI()
            logger.info("✅ SauAI inicializado correctamente en BotCore")
        except Exception as e:
            logger.error(f"❌ Error al inicializar SauAI en BotCore: {e}")
            raise
        
        # Asignar gestores de sesiones y usuarios
        self.session_manager = session_manager
        self.user_manager = user_manager
        
        # Inicializar ThreadPoolExecutor para procesamiento concurrente
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="BotCore-")
        
        logger.info("✅ BotCore inicializado correctamente")
    
    async def process_message(self, message_input: MessageInput) -> MessageResponse:
        """
        Procesa un mensaje de forma genérica, independiente de la plataforma
        
        Args:
            message_input: Datos del mensaje en formato genérico
            
        Returns:
            MessageResponse: Respuesta en formato genérico
        """
        try:
            logger.info(f"🔄 Procesando mensaje de {message_input.username} desde {message_input.origin}")
            
            # 1. Obtener o crear sesión del usuario
            user_session = await self._safe_session_operation(message_input.username)
            
            # 2. Guardar mensaje del usuario en historial
            await self._safe_add_message(user_session.session_id, message_input.message, is_user=True)
            
            # 3. Procesar mensaje con SauAI
            response_content = await self._safe_process_with_sauai(
                message_input.username, 
                user_session.session_id, 
                message_input.message
            )
            
            # 4. Guardar respuesta en historial
            await self._safe_add_message(user_session.session_id, response_content, is_user=False)
            
            # 5. Retornar respuesta genérica
            return MessageResponse(
                content=response_content,
                response_type="text",
                metadata={
                    "session_id": str(user_session.session_id),
                    "username": message_input.username,
                    "origin": message_input.origin,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje de {message_input.username}: {e}")
            return MessageResponse(
                content="❌ Lo siento, ocurrió un error al procesar tu pregunta. Por favor, intenta nuevamente.",
                response_type="error",
                metadata={
                    "error": str(e),
                    "username": message_input.username,
                    "origin": message_input.origin,
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    async def _safe_session_operation(self, username: str):
        """Operación segura para obtener/crear sesión con reintentos"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                
                # Primero verificar si el usuario existe, si no, crearlo
                user_info = await loop.run_in_executor(
                    self.executor,
                    self.user_manager.get_user,
                    username
                )
                
                if not user_info:
                    # Crear usuario web automáticamente
                    logger.info(f"🆕 Creando usuario web automáticamente: {username}")
                    await loop.run_in_executor(
                        self.executor,
                        self.user_manager.create_web_user,
                        username,
                        username.replace('@', ''),  # Usar username como nombre
                        ""  # Email vacío
                    )
                
                # Ahora crear/obtener la sesión
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
        """
        Procesa un mensaje con SauAI - LÓGICA CENTRAL EXTRAÍDA DE TELEGRAM_BOT.PY
        
        Esta es la lógica de negocio principal que se mantiene igual independientemente
        de si el mensaje viene de Telegram, web, o cualquier otra plataforma.
        """
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
    
    def get_typing_response(self, duration: int = 3) -> MessageResponse:
        """
        Genera una respuesta de "typing" genérica
        
        Args:
            duration: Duración en segundos del indicador de typing
            
        Returns:
            MessageResponse: Respuesta de tipo "typing"
        """
        return MessageResponse(
            content="",
            response_type="typing",
            metadata={"duration": duration}
        )
    
    def get_error_response(self, error_message: str = "Error interno del servidor") -> MessageResponse:
        """
        Genera una respuesta de error genérica
        
        Args:
            error_message: Mensaje de error personalizado
            
        Returns:
            MessageResponse: Respuesta de tipo "error"
        """
        return MessageResponse(
            content=f"❌ {error_message}",
            response_type="error",
            metadata={"timestamp": datetime.now().isoformat()}
        )
    
    def cleanup(self):
        """Limpia recursos al cerrar el bot"""
        logger.info("🧹 Limpiando recursos de BotCore...")
        try:
            if hasattr(self, 'executor') and self.executor:
                self.executor.shutdown(wait=True, cancel_futures=True)
                logger.info("✅ ThreadPoolExecutor de BotCore cerrado correctamente")
        except Exception as e:
            logger.error(f"❌ Error durante cleanup de BotCore: {e}")

# Funciones de conveniencia para uso directo
async def process_message_async(
    username: str, 
    message: str, 
    origin: str = "unknown",
    user_manager: UserManager = None,
    session_manager: SessionManager = None,
    bot_core: BotCore = None
) -> MessageResponse:
    """
    Función de conveniencia para procesar un mensaje de forma asíncrona
    
    Args:
        username: Username del usuario
        message: Contenido del mensaje
        origin: Origen del mensaje ("telegram", "web", etc.)
        user_manager: Instancia de UserManager (opcional si se pasa bot_core)
        session_manager: Instancia de SessionManager (opcional si se pasa bot_core)
        bot_core: Instancia de BotCore (opcional, se crea si no se proporciona)
        
    Returns:
        MessageResponse: Respuesta procesada
    """
    if bot_core is None:
        if user_manager is None or session_manager is None:
            raise ValueError("Debe proporcionar bot_core o ambos user_manager y session_manager")
        bot_core = BotCore(user_manager, session_manager)
    
    message_input = MessageInput(
        username=username,
        message=message,
        origin=origin
    )
    
    return await bot_core.process_message(message_input)
