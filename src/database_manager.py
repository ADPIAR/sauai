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
            # Tabla users
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    username VARCHAR(255),
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

            # Tabla sessions
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_preferences JSONB DEFAULT '{}'::jsonb
                );
            """)

            # Tabla conversation_messages
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
            print("Tablas verificadas/creadas exitosamente.")
        except Exception as e:
            self.conn.rollback()
            print(f"Error al crear/verificar tablas: {e}")
            raise

if __name__ == '__main__':
    # Este bloque solo es para probar la conexión y creación de tablas
    # Asegúrate de tener la variable de entorno DATABASE_URL configurada
    try:
        db_manager = DatabaseManager()
        db_manager.close()
    except Exception as e:
        print(f"Fallo en la prueba del DatabaseManager: {e}") 