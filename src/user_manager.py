#!/usr/bin/env python3
"""
Gestor de usuarios para el bot de Telegram
"""

import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict, field
from database_manager import DatabaseManager # Importa DatabaseManager

@dataclass
class UserInfo:
    """Información de un usuario del bot de Telegram"""
    username: str  # Primary key - username de Telegram
    telegram_user_id: int  # ID único de Telegram
    first_name: str = ""
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: bool = False
    first_seen: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_seen: datetime.datetime = field(default_factory=datetime.datetime.now)
    message_count: int = 0
    favorite_topics: List[str] = field(default_factory=list)
    personal_name: Optional[str] = None
    age: Optional[int] = None
    user_needs: Optional[str] = None

    def to_dict(self):
        # Convierte el objeto UserInfo a un diccionario, incluyendo el formato de fecha ISO
        data = asdict(self)
        data['first_seen'] = self.first_seen.isoformat()
        data['last_seen'] = self.last_seen.isoformat()
        return data

class UserManager:
    """Gestiona información de usuarios del bot usando PostgreSQL"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_user(self, username: str) -> Optional[UserInfo]:
        """Obtiene un usuario de la base de datos por su username."""
        try:
            with self.db_manager.get_connection() as (conn, cursor):
                cursor.execute(
                    "SELECT username, telegram_user_id, first_name, last_name, language_code, is_premium, first_seen, last_seen, message_count, favorite_topics, personal_name, age, user_needs FROM users_telegram WHERE username = %s;",
                    (username,)
                )
                row = cursor.fetchone()
                if row:
                    return UserInfo(
                        username=row[0],
                        telegram_user_id=row[1],
                        first_name=row[2],
                        last_name=row[3],
                        language_code=row[4],
                        is_premium=row[5],
                        first_seen=row[6],
                        last_seen=row[7],
                        message_count=row[8],
                        favorite_topics=row[9] if row[9] else [],
                        personal_name=row[10],
                        age=row[11],
                        user_needs=row[12]
                    )
                return None
        except Exception as e:
            print(f"Error al obtener usuario {username}: {e}")
            return None

    def create_or_update_user(self, user_data) -> UserInfo:
        """Crea o actualiza un usuario en la base de datos."""
        telegram_user_id = user_data.id
        username = user_data.username or f"user_{telegram_user_id}"  # Usar username o crear uno temporal
        now = datetime.datetime.now()

        existing_user = self.get_user(username)

        if existing_user:
            # Actualizar usuario existente
            sql = """
                UPDATE users_telegram
                SET telegram_user_id = %s, first_name = %s, last_name = %s,
                    language_code = %s, is_premium = %s, last_seen = %s,
                    message_count = message_count + 1
                WHERE username = %s
                RETURNING *;
            """
            params = (
                telegram_user_id, user_data.first_name, user_data.last_name,
                user_data.language_code, getattr(user_data, 'is_premium', False),
                now, username
            )
        else:
            # Nuevo usuario
            sql = """
                INSERT INTO users_telegram (username, telegram_user_id, first_name, last_name,
                                   language_code, is_premium, first_seen,
                                   last_seen, message_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *;
            """
            params = (
                username, telegram_user_id, user_data.first_name, user_data.last_name,
                user_data.language_code,
                getattr(user_data, 'is_premium', False), now, now, 1
            )

        try:
            with self.db_manager.get_connection() as (conn, cursor):
                cursor.execute(sql, params)
                conn.commit()
                updated_user_row = cursor.fetchone()
                if updated_user_row:
                    return UserInfo(
                        username=updated_user_row[0],
                        telegram_user_id=updated_user_row[1],
                        first_name=updated_user_row[2],
                        last_name=updated_user_row[3],
                        language_code=updated_user_row[4],
                        is_premium=updated_user_row[5],
                        first_seen=updated_user_row[6],
                        last_seen=updated_user_row[7],
                        message_count=updated_user_row[8],
                        favorite_topics=updated_user_row[9] if updated_user_row[9] else [],
                        personal_name=updated_user_row[10],
                        age=updated_user_row[11],
                        user_needs=updated_user_row[12]
                    )
                raise Exception("No se pudo recuperar el usuario después de la inserción/actualización.")
        except Exception as e:
            print(f"Error al registrar/actualizar usuario {username}: {e}")
            raise

    def increment_message_count(self, username: str):
        """Incrementa el contador de mensajes de un usuario."""
        try:
            with self.db_manager.get_connection() as (conn, cursor):
                cursor.execute(
                    "UPDATE users_telegram SET message_count = message_count + 1, last_seen = %s WHERE username = %s;",
                    (datetime.datetime.now(), username)
                )
                conn.commit()
        except Exception as e:
            print(f"Error al incrementar contador de mensajes para el usuario {username}: {e}")
            raise

    def track_topic_interest(self, username: str, topic: str):
        """Registra interés en un tema específico para un usuario."""
        try:
            with self.db_manager.get_connection() as (conn, cursor):
                # Añade el tema al array si no existe
                cursor.execute(
                    "UPDATE users_telegram SET favorite_topics = array_append(favorite_topics, %s) WHERE username = %s AND NOT (%s = ANY(favorite_topics));",
                    (topic, username, topic)
                )
                conn.commit()
        except Exception as e:
            print(f"Error al registrar interés en el tema '{topic}' para el usuario {username}: {e}")
            raise

    def get_user_stats(self) -> Dict:
        """Obtiene estadísticas generales de los usuarios."""
        try:
            with self.db_manager.get_connection() as (conn, cursor):
                cursor.execute("SELECT COUNT(*) FROM users_telegram;")
                total_users = cursor.fetchone()[0]

                today = datetime.datetime.now().date()
                cursor.execute(
                    "SELECT COUNT(*) FROM users_telegram WHERE last_seen::date = %s;",
                    (today,)
                )
                active_today = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT first_name, message_count FROM users_telegram ORDER BY message_count DESC LIMIT 10;"
                )
                top_users_rows = cursor.fetchall()
                top_users = [{"first_name": row[0], "message_count": row[1]} for row in top_users_rows]

                cursor.execute(
                    "SELECT language_code, COUNT(*) FROM users_telegram WHERE language_code IS NOT NULL GROUP BY language_code;"
                )
                languages_rows = cursor.fetchall()
                languages = {row[0]: row[1] for row in languages_rows}

                return {
                    "total_users": total_users,
                    "active_today": active_today,
                    "top_users": top_users,
                    "languages": languages
                }
        except Exception as e:
            print(f"Error al obtener estadísticas de usuarios: {e}")
            return {}

    def create_web_user(self, username: str, name: str = "", email: str = "") -> UserInfo:
        """
        Crea un usuario web en la base de datos.
        
        Args:
            username: Username del usuario (ej: @test)
            name: Nombre del usuario
            email: Email del usuario
            
        Returns:
            UserInfo: Información del usuario creado
        """
        try:
            with self.db_manager.get_connection() as (conn, cursor):
                # Verificar si el usuario ya existe
                existing_user = self.get_user(username)
                if existing_user:
                    return existing_user
                
                # Primero crear el usuario en la tabla users
                user_sql = """
                    INSERT INTO users (telegram_username, name, email, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                """
                now = datetime.datetime.now()
                user_params = (username, name, email, now, now)
                
                cursor.execute(user_sql, user_params)
                user_id = cursor.fetchone()[0]
                
                # Luego crear el usuario en users_telegram sin telegram_user_id (será NULL)
                telegram_sql = """
                    INSERT INTO users_telegram (username, telegram_user_id, first_name, last_name,
                                       language_code, is_premium, first_seen,
                                       last_seen, message_count, personal_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *;
                """
                telegram_params = (
                    username, None, name, "", "es", False, 
                    now, now, 0, name
                )
                
                cursor.execute(telegram_sql, telegram_params)
                conn.commit()
                new_user_row = cursor.fetchone()
                
                if new_user_row:
                    return UserInfo(
                        username=new_user_row[0],
                        telegram_user_id=new_user_row[1] if new_user_row[1] else 0,  # 0 para usuarios web
                        first_name=new_user_row[2],
                        last_name=new_user_row[3],
                        language_code=new_user_row[4],
                        is_premium=new_user_row[5],
                        first_seen=new_user_row[6],
                        last_seen=new_user_row[7],
                        message_count=new_user_row[8],
                        favorite_topics=new_user_row[9] if new_user_row[9] else [],
                        personal_name=new_user_row[10],
                        age=new_user_row[11],
                        user_needs=new_user_row[12]
                    )
                else:
                    raise Exception("No se pudo crear el usuario web")
                    
        except Exception as e:
            print(f"Error al crear usuario web {username}: {e}")
            raise