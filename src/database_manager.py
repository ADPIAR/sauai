import os
import psycopg2
import uuid
from urllib.parse import urlparse

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set.")
        self._connect()
        self.create_tables()

    def _connect(self):
        try:
            url = urlparse(self.database_url)
            self.conn = psycopg2.connect(
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port
            )
            self.cursor = self.conn.cursor()
            print("Conexión a la base de datos PostgreSQL exitosa.")
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")
            raise

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Conexión a la base de datos PostgreSQL cerrada.")

    def create_tables(self):
        try:
            # Tabla users_telegram - Nueva tabla para usuarios de Telegram
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_telegram (
                    username VARCHAR(255) PRIMARY KEY,
                    telegram_user_id BIGINT UNIQUE NOT NULL,
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
                    user_needs TEXT,
                    FOREIGN KEY (username) REFERENCES users(telegram_username) ON DELETE CASCADE
                );
            """)
            self.conn.commit()
            print("✅ Tabla 'users_telegram' creada/verificada")

            # Tabla sessions - Crear después de users_telegram
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(255) REFERENCES users_telegram(username) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_preferences JSONB DEFAULT '{}'::jsonb
                );
            """)
            self.conn.commit()
            print("✅ Tabla 'sessions' creada/verificada")

            # Tabla conversation_messages - Crear después de sessions
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID REFERENCES sessions(session_id) ON DELETE CASCADE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message TEXT,
                    is_user BOOLEAN
                );
            """)
            self.conn.commit()
            print("✅ Tabla 'conversation_messages' creada/verificada")
            print("✅ Todas las tablas verificadas/creadas exitosamente.")
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Error al crear/verificar tablas: {e}")
            raise

if __name__ == '__main__':
    # Este bloque solo es para probar la conexión y creación de tablas
    # Asegúrate de tener la variable de entorno DATABASE_URL configurada
    try:
        db_manager = DatabaseManager()
        db_manager.close()
    except Exception as e:
        print(f"Fallo en la prueba del DatabaseManager: {e}") 