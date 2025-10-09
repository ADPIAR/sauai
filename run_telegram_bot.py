#!/usr/bin/env python3
"""
Script para ejecutar el bot de Telegram de SauAI
"""

import sys
import os
import logging

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('telegram_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Agregar directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importar las clases recién actualizadas
from src.database_manager import DatabaseManager
from src.user_manager import UserManager
from src.session_manager import SessionManager

def check_requirements():
    """Verifica que los requirements estén instalados"""
    try:
        import telegram
        import dotenv
        from pinecone import Pinecone
        import openai
        import langchain
        import psycopg2
        return True
    except ImportError as e:
        logger.error(f"❌ Dependencia faltante: {e}")
        logger.error("💡 Instala las dependencias con: pip install -r requirements.txt")
        return False

def check_environment():
    """Verifica que las variables de entorno estén configuradas"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['OPENAI_API_KEY', 'PINECONE_API_KEY', 'TELEGRAM_BOT_TOKEN', 'DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
        logger.error("💡 Configura tu archivo .env con las API keys necesarias")
        return False
    
    return True

def main():
    """Función principal para ejecutar el bot"""
    print("🌟 INICIANDO SAÚAI BOT PARA TELEGRAM")
    print("="*50)
    
    # Verificar requirements
    logger.info("🔍 Verificando dependencias...")
    if not check_requirements():
        sys.exit(1)
    logger.info("✅ Dependencias verificadas")
    
    # Verificar variables de entorno
    logger.info("🔍 Verificando variables de entorno...")
    if not check_environment():
        sys.exit(1)
    logger.info("✅ Variables de entorno verificadas")
    
    # Inicializar DatabaseManager, UserManager y SessionManager
    db_manager = None
    try:
        logger.info("📦 Inicializando DatabaseManager...")
        db_manager = DatabaseManager()
        logger.info("✅ DatabaseManager inicializado y tablas verificadas/creadas.")
        
        logger.info("👨‍💻 Inicializando UserManager...")
        user_manager = UserManager(db_manager)
        logger.info("✅ UserManager inicializado.")
        
        logger.info("🔄 Inicializando SessionManager...")
        session_manager = SessionManager(db_manager)
        logger.info("✅ SessionManager inicializado.")
        
        logger.info("📱 Importando bot de Telegram...")
        from src.telegram_bot import TelegramSauAI
        
        logger.info("🚀 Iniciando bot...")
        bot = TelegramSauAI(user_manager=user_manager, session_manager=session_manager) # Pasar los managers
        
        logger.info("✅ Bot iniciado exitosamente")
        logger.info("💬 El bot está listo para recibir mensajes")
        logger.info("🛑 Presiona Ctrl+C para detener el bot")
        
        # Ejecutar el bot
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("\n👋 Bot detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        logger.error("💡 Revisa los logs arriba para más detalles")
        sys.exit(1)
    finally:
        if db_manager:
            db_manager.close()
            logger.info("🔌 Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    main() 