#!/usr/bin/env python3
"""
Script para ejecutar el bot SAÚ AI con interfaz web
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
        logging.FileHandler('web_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Agregar directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def check_requirements():
    """Verifica que los requirements estén instalados"""
    try:
        import flask
        import flask_cors
        from dotenv import load_dotenv
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
    
    required_vars = ['OPENAI_API_KEY', 'PINECONE_API_KEY', 'DATABASE_URL']
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
    """Función principal para ejecutar el bot web"""
    print("🌐 INICIANDO SAÚAI BOT WEB")
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
        from src.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        logger.info("✅ DatabaseManager inicializado y tablas verificadas/creadas.")
        
        logger.info("👨‍💻 Inicializando UserManager...")
        from src.user_manager import UserManager
        user_manager = UserManager(db_manager)
        logger.info("✅ UserManager inicializado.")
        
        logger.info("🔄 Inicializando SessionManager...")
        from src.session_manager import SessionManager
        session_manager = SessionManager(db_manager)
        logger.info("✅ SessionManager inicializado.")
        
        logger.info("🌐 Iniciando servidor web...")
        from src.web_handler import create_web_handler
        
        web_handler = create_web_handler(user_manager, session_manager)
        
        # Obtener puerto de Railway o usar 5000 por defecto
        port = int(os.getenv('PORT', 5000))
        host = os.getenv('HOST', '0.0.0.0')
        
        # Logs críticos para Railway
        print(f"🚀 SAÚ AI Backend iniciando en puerto {port}")
        print(f"🌐 Host configurado: {host}")
        print(f"🔧 Variable PORT: {os.getenv('PORT', 'NO_DEFINIDA')}")
        print(f"🔧 Variable HOST: {os.getenv('HOST', 'NO_DEFINIDA')}")
        
        logger.info(f"✅ Servidor web iniciado en {host}:{port}")
        logger.info("💬 El bot está listo para recibir mensajes web")
        logger.info("🛑 Presiona Ctrl+C para detener el servidor")
        
        # Ejecutar el servidor web
        web_handler.run(host=host, port=port, debug=False)
        
    except KeyboardInterrupt:
        logger.info("\n👋 Servidor web detenido por el usuario")
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
