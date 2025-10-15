import os
import psycopg2
import psycopg2.pool
import uuid
import time
import logging
from urllib.parse import urlparse
from contextlib import contextmanager

# Configurar logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, max_connections=10, min_connections=1):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set.")
        
        # Configurar pool de conexiones
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.connection_pool = None
        self._setup_connection_pool()
        self.create_tables()

    def _setup_connection_pool(self):
        """Configura el pool de conexiones con reconexión automática"""
        try:
            url = urlparse(self.database_url)
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port,
                # Configuraciones para mejorar la estabilidad
                connect_timeout=10,
                application_name='sau-bot',
                keepalives=1,
                keepalives_idle=600,
                keepalives_interval=30,
                keepalives_count=3
            )
            logger.info("✅ Pool de conexiones PostgreSQL configurado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error al configurar pool de conexiones: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager para obtener una conexión del pool con manejo automático de errores"""
        conn = None
        cursor = None
        try:
            # Verificar si el pool está disponible
            if not self.connection_pool:
                logger.warning("⚠️ Pool de conexiones no disponible, intentando reconectar...")
                self._reconnect()
            
            conn = self.connection_pool.getconn()
            if conn is None:
                raise Exception("No se pudo obtener conexión del pool")
            cursor = conn.cursor()
            yield conn, cursor
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logger.warning(f"⚠️ Error de conexión detectado: {e}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            # Intentar reconectar solo si el error es de conexión
            if "connection" in str(e).lower() or "pool" in str(e).lower():
                self._reconnect()
            raise
        except Exception as e:
            logger.error(f"❌ Error en operación de base de datos: {e}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception as e:
                    logger.debug(f"Error cerrando cursor: {e}")
            if conn and self.connection_pool:
                try:
                    self.connection_pool.putconn(conn)
                except Exception as e:
                    logger.error(f"❌ Error al devolver conexión al pool: {e}")
                    # No re-raise aquí para evitar el error "trying to put unkeyed connection"

    def _reconnect(self):
        """Reconecta el pool de conexiones en caso de error"""
        try:
            logger.info("🔄 Intentando reconectar a la base de datos...")
            # Cerrar pool existente de forma segura
            if self.connection_pool:
                try:
                    self.connection_pool.closeall()
                except Exception as e:
                    logger.debug(f"Error cerrando pool existente: {e}")
                self.connection_pool = None
            
            # Esperar antes de reconectar
            time.sleep(2)
            
            # Crear nuevo pool
            self._setup_connection_pool()
            logger.info("✅ Reconexión exitosa")
        except Exception as e:
            logger.error(f"❌ Error durante reconexión: {e}")
            self.connection_pool = None
            raise

    def _connect(self):
        """Método legacy mantenido para compatibilidad"""
        with self.get_connection() as (conn, cursor):
            pass

    def close(self):
        """Cierra el pool de conexiones"""
        try:
            if self.connection_pool:
                self.connection_pool.closeall()
                logger.info("🔌 Pool de conexiones PostgreSQL cerrado correctamente")
        except Exception as e:
            logger.error(f"❌ Error al cerrar pool de conexiones: {e}")

    def create_tables(self):
        """Crea las tablas necesarias usando el pool de conexiones"""
        try:
            with self.get_connection() as (conn, cursor):
                # Tabla users_telegram - Nueva tabla para usuarios de Telegram
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users_telegram (
                        username VARCHAR(255) PRIMARY KEY,
                        telegram_user_id BIGINT UNIQUE,
                        first_name VARCHAR(255),
                        last_name VARCHAR(255),
                        language_code VARCHAR(10),
                        is_premium BOOLEAN,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        message_count INTEGER DEFAULT 0,
                        favorite_topics TEXT[] DEFAULT ARRAY[]::TEXT[],
                        personal_name VARCHAR(255),
                        age INTEGER,
                        user_needs TEXT
                    );
                """)
                conn.commit()
                logger.info("✅ Tabla 'users_telegram' creada/verificada")

                # Tabla sessions - Crear después de users_telegram
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        username VARCHAR(255) REFERENCES users_telegram(username) ON DELETE CASCADE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_preferences JSONB DEFAULT '{}'::jsonb
                    );
                """)
                conn.commit()
                logger.info("✅ Tabla 'sessions' creada/verificada")

                # Tabla conversation_messages - Crear después de sessions
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_messages (
                        message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        session_id UUID REFERENCES sessions(session_id) ON DELETE CASCADE,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        message TEXT,
                        is_user BOOLEAN
                    );
                """)
                conn.commit()
                logger.info("✅ Tabla 'conversation_messages' creada/verificada")
                logger.info("✅ Todas las tablas verificadas/creadas exitosamente")
        except Exception as e:
            logger.error(f"❌ Error al crear/verificar tablas: {e}")
            raise

if __name__ == '__main__':
    # Este bloque solo es para probar la conexión y creación de tablas
    # Asegúrate de tener la variable de entorno DATABASE_URL configurada
    try:
        db_manager = DatabaseManager()
        db_manager.close()
    except Exception as e:
        print(f"Fallo en la prueba del DatabaseManager: {e}") 