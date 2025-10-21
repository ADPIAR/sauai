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
            
            # Configuraciones optimizadas para Railway
            connection_params = {
                'database': url.path[1:],
                'user': url.username,
                'password': url.password,
                'host': url.hostname,
                'port': url.port,
                # Timeouts más largos para Railway
                'connect_timeout': 60,
                'application_name': 'sau-bot',
                # Keepalive para Railway
                'keepalives': 1,
                'keepalives_idle': 600,  # 10 minutos
                'keepalives_interval': 30,
                'keepalives_count': 5,
                # SSL optimizado para Railway
                'sslmode': 'require',
                'sslcert': None,
                'sslkey': None,
                'sslrootcert': None
            }
            
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                **connection_params
            )
            logger.info("✅ Pool de conexiones PostgreSQL configurado exitosamente")
            logger.info(f"🔧 Configuración: host={url.hostname}, port={url.port}, db={url.path[1:]}")
        except Exception as e:
            logger.error(f"❌ Error al configurar pool de conexiones: {e}")
            logger.error(f"🔧 DATABASE_URL: {self.database_url[:50]}...")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager para obtener una conexión del pool con manejo automático de errores"""
        conn = None
        cursor = None
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Verificar si el pool está disponible
                if not self.connection_pool:
                    logger.warning("⚠️ Pool de conexiones no disponible, intentando reconectar...")
                    self._reconnect()
                
                logger.debug(f"🔄 Intento {retry_count + 1} de obtener conexión del pool")
                conn = self.connection_pool.getconn()
                if conn is None:
                    raise Exception("No se pudo obtener conexión del pool")
                
                # Verificar que la conexión esté activa
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                
                logger.debug("✅ Conexión obtenida y verificada exitosamente")
                yield conn, cursor
                return  # Éxito, salir del bucle
                
            except (psycopg2.OperationalError, psycopg2.InterfaceError, psycopg2.DatabaseError) as e:
                retry_count += 1
                logger.warning(f"⚠️ Error de conexión detectado (intento {retry_count}/{max_retries}): {e}")
                
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                
                # Intentar reconectar solo si el error es de conexión
                if any(keyword in str(e).lower() for keyword in ["connection", "pool", "timeout", "server"]):
                    if retry_count < max_retries:
                        logger.info(f"🔄 Intentando reconectar... (intento {retry_count})")
                        self._reconnect()
                        time.sleep(1)  # Esperar antes del siguiente intento
                        continue
                
                if retry_count >= max_retries:
                    logger.error(f"❌ Falló después de {max_retries} intentos: {e}")
                    raise
                    
            except Exception as e:
                logger.error(f"❌ Error inesperado en operación de base de datos: {e}")
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
                        logger.debug("✅ Conexión devuelta al pool")
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
                    logger.debug("🔌 Cerrando pool de conexiones existente...")
                    self.connection_pool.closeall()
                except Exception as e:
                    logger.debug(f"Error cerrando pool existente: {e}")
                finally:
                    self.connection_pool = None
            
            # Esperar antes de reconectar (backoff exponencial)
            wait_time = min(2, 10)  # 2 segundos por defecto
            logger.info(f"⏳ Esperando {wait_time} segundos antes de reconectar...")
            time.sleep(wait_time)
            
            # Crear nuevo pool
            logger.info("🔧 Creando nuevo pool de conexiones...")
            self._setup_connection_pool()
            
            # Verificar que el nuevo pool funciona
            with self.get_connection() as (conn, cursor):
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            logger.info("✅ Reconexión exitosa y verificada")
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

    def health_check(self):
        """Verifica la salud de la conexión a la base de datos"""
        try:
            with self.get_connection() as (conn, cursor):
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    logger.info("✅ Health check de base de datos exitoso")
                    return True
                else:
                    logger.warning("⚠️ Health check de base de datos falló")
                    return False
        except Exception as e:
            logger.error(f"❌ Health check de base de datos falló: {e}")
            return False

    def create_tables(self):
        """Crea las tablas necesarias usando el pool de conexiones"""
        try:
            logger.info("🔧 Iniciando creación/verificación de tablas...")
            with self.get_connection() as (conn, cursor):
                # Tabla sessions (ya sin FK a users_telegram)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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