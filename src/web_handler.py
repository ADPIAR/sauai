#!/usr/bin/env python3
"""
Web Handler - Ejemplo de integración web para el bot SAÚ AI
Este archivo muestra cómo integrar el BotCore con una API web
"""

import logging
import asyncio
from typing import Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS

from bot_core import BotCore, MessageInput, MessageResponse
from database_manager import DatabaseManager
from user_manager import UserManager
from session_manager import SessionManager

# Configurar logging
logger = logging.getLogger(__name__)

class WebHandler:
    """
    Handler para integración web del bot SAÚ AI
    Demuestra cómo usar BotCore desde una API web
    """
    
    def __init__(self, bot_core: BotCore):
        """Inicializa el handler web con BotCore"""
        self.bot_core = bot_core
        self.app = Flask(__name__)
        CORS(self.app, origins=[
            "https://gamersmed.apversus.com",  # Producción APV-Web
            "https://apv-web-git-dev-adpiars-projects.vercel.app",  # Desarrollo APV-Web
            "http://localhost:3000"  # Desarrollo local
        ])
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la API web"""
        
        @self.app.route('/api/chat', methods=['POST'])
        def chat_endpoint():
            """
            Endpoint para procesar mensajes desde la web
            
            Formato esperado:
            {
                "username": "@usuario",
                "message": "Hola, ¿cómo estás?",
                "metadata": {
                    "user_agent": "...",
                    "ip": "..."
                }
            }
            
            Respuesta:
            {
                "success": true,
                "response": {
                    "content": "¡Hola! Soy SAÚ...",
                    "response_type": "text",
                    "metadata": {
                        "session_id": "uuid",
                        "timestamp": "2024-01-01T12:00:00"
                    }
                }
            }
            """
            try:
                data = request.get_json()
                
                # Validar datos de entrada
                if not data or 'username' not in data or 'message' not in data:
                    return jsonify({
                        "success": False,
                        "error": "Se requieren 'username' y 'message'"
                    }), 400
                
                # Crear entrada de mensaje genérica
                message_input = MessageInput(
                    username=data['username'],
                    message=data['message'],
                    origin="web",
                    metadata={
                        "user_agent": request.headers.get('User-Agent'),
                        "ip": request.remote_addr,
                        **data.get('metadata', {})
                    }
                )
                
                # Procesar mensaje usando BotCore (síncrono)
                response = asyncio.run(self.bot_core.process_message(message_input))
                
                # Retornar respuesta en formato JSON
                return jsonify({
                    "success": True,
                    "response": {
                        "content": response.content,
                        "response_type": response.response_type,
                        "metadata": response.metadata
                    }
                })
                
            except Exception as e:
                logger.error(f"Error en endpoint /api/chat: {e}")
                return jsonify({
                    "success": False,
                    "error": "Error interno del servidor"
                }), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Endpoint de salud para verificar que el servicio está funcionando"""
            return jsonify({
                "status": "healthy",
                "message": "SAÚ AI Backend is running",
                "service": "SAÚ AI Web API",
                "version": "1.0.0",
                "endpoints": {
                    "chat": "/api/chat",
                    "check_user": "/api/check-user",
                    "typing": "/api/typing"
                }
            })
        
        @self.app.route('/api/check-user', methods=['POST'])
        def check_user_endpoint():
            """
            Verifica si usuario APV-Web existe en users_telegram
            Si no existe, lo crea automáticamente
            
            Request:
            {
                "apv_user_id": "uuid",
                "email": "user@example.com",
                "name": "Juan Pérez"
            }
            
            Response:
            {
                "success": true,
                "username": "@juan.perez",
                "exists": true,
                "message": "Usuario verificado correctamente"
            }
            """
            try:
                data = request.get_json()
                
                if not data or 'email' not in data:
                    return jsonify({
                        "success": False,
                        "error": "Se requieren 'email' en el request"
                    }), 400
                
                apv_user_id = data.get('apv_user_id', '')
                email = data['email']
                name = data.get('name', '')
                
                # Generar @username automáticamente basado en email
                username = f"@{email.split('@')[0]}"
                
                # Verificar si el usuario ya existe en users_telegram
                # Por ahora, asumimos que no existe y se creará automáticamente
                # cuando haga su primer mensaje
                
                return jsonify({
                    "success": True,
                    "username": username,
                    "exists": False,  # Se creará automáticamente en el primer mensaje
                    "message": "Usuario listo para usar SAÚ AI"
                })
                
            except Exception as e:
                logger.error(f"Error en endpoint /api/check-user: {e}")
                return jsonify({
                    "success": False,
                    "error": "Error interno del servidor"
                }), 500
        
        @self.app.route('/api/typing', methods=['POST'])
        def typing_endpoint():
            """
            Endpoint para simular indicador de typing
            Útil para mostrar que el bot está procesando
            """
            try:
                data = request.get_json()
                duration = data.get('duration', 3) if data else 3
                
                # Generar respuesta de typing
                response = self.bot_core.get_typing_response(duration)
                
                return jsonify({
                    "success": True,
                    "response": {
                        "response_type": response.response_type,
                        "metadata": response.metadata
                    }
                })
                
            except Exception as e:
                logger.error(f"Error en endpoint /api/typing: {e}")
                return jsonify({
                    "success": False,
                    "error": "Error interno del servidor"
                }), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Ejecuta el servidor web"""
        print(f"🌐 SAÚ AI Web Server iniciando en {host}:{port}")
        print(f"🔗 Health check disponible en: http://{host}:{port}/api/health")
        logger.info(f"🌐 Iniciando servidor web en {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# Función de conveniencia para crear el handler web
def create_web_handler(
    user_manager: UserManager,
    session_manager: SessionManager
) -> WebHandler:
    """
    Crea un WebHandler con BotCore inicializado
    
    Args:
        user_manager: Instancia de UserManager
        session_manager: Instancia de SessionManager
        
    Returns:
        WebHandler: Handler web configurado
    """
    bot_core = BotCore(user_manager, session_manager)
    return WebHandler(bot_core)

# Ejemplo de uso (no se ejecuta automáticamente)
if __name__ == "__main__":
    # Este bloque solo se ejecuta si se llama directamente
    # En producción, esto se manejaría desde el archivo principal
    
    print("⚠️  Este archivo es solo un ejemplo de integración web")
    print("💡 Para usar en producción, integra WebHandler en tu aplicación principal")
    print("📝 Ejemplo de uso:")
    print("""
    # En tu aplicación principal:
    from src.web_handler import create_web_handler
    
    # Inicializar managers
    db_manager = DatabaseManager()
    user_manager = UserManager(db_manager)
    session_manager = SessionManager(db_manager)
    
    # Crear handler web
    web_handler = create_web_handler(user_manager, session_manager)
    
    # Ejecutar servidor
    web_handler.run(host='0.0.0.0', port=5000)
    """)
