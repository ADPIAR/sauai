#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de conexión a la base de datos
"""

import os
import sys
import logging
from urllib.parse import urlparse

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_environment():
    """Verifica las variables de entorno"""
    logger.info("🔍 Verificando variables de entorno...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL no está configurada")
        return False
    
    logger.info(f"✅ DATABASE_URL configurada: {database_url[:50]}...")
    
    # Parsear la URL para verificar formato
    try:
        url = urlparse(database_url)
        logger.info(f"🔧 Host: {url.hostname}")
        logger.info(f"🔧 Puerto: {url.port}")
        logger.info(f"🔧 Base de datos: {url.path[1:]}")
        logger.info(f"🔧 Usuario: {url.username}")
        return True
    except Exception as e:
        logger.error(f"❌ Error parseando DATABASE_URL: {e}")
        return False

def test_connection():
    """Prueba la conexión a la base de datos"""
    logger.info("🔍 Probando conexión a la base de datos...")
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        database_url = os.getenv('DATABASE_URL')
        url = urlparse(database_url)
        
        # Configuración optimizada para Railway
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            connect_timeout=60,
            sslmode='require',
            application_name='sau-bot-diagnose'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        logger.info(f"✅ Conexión exitosa a PostgreSQL: {version[0][:50]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error de conexión: {e}")
        return False

def test_database_manager():
    """Prueba el DatabaseManager"""
    logger.info("🔍 Probando DatabaseManager...")
    
    try:
        sys.path.append('src')
        from database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # Health check
        if db_manager.health_check():
            logger.info("✅ DatabaseManager health check exitoso")
        else:
            logger.error("❌ DatabaseManager health check falló")
            return False
        
        # Probar operación básica
        with db_manager.get_connection() as (conn, cursor):
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                logger.info("✅ Operación básica exitosa")
            else:
                logger.error("❌ Operación básica falló")
                return False
        
        db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en DatabaseManager: {e}")
        return False

def main():
    """Función principal de diagnóstico"""
    print("🔧 DIAGNÓSTICO DE BASE DE DATOS SAÚ AI")
    print("=" * 50)
    
    # Verificar variables de entorno
    if not check_environment():
        logger.error("❌ Variables de entorno no configuradas correctamente")
        sys.exit(1)
    
    # Probar conexión directa
    if not test_connection():
        logger.error("❌ Conexión directa falló")
        sys.exit(1)
    
    # Probar DatabaseManager
    if not test_database_manager():
        logger.error("❌ DatabaseManager falló")
        sys.exit(1)
    
    logger.info("✅ Todos los diagnósticos pasaron exitosamente")
    print("🎉 La configuración de la base de datos está funcionando correctamente")

if __name__ == "__main__":
    main()
