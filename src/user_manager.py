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
    """Información de un usuario desde tabla users"""
    telegram_username: str  # Primary key desde users
    session_id: Optional[str] = None  # Nueva columna
    name: str = ""
    email: str = ""
    message_count: int = 0  # Contador de mensajes migrado desde users_telegram
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

    def to_dict(self):
        # Convierte el objeto UserInfo a un diccionario, incluyendo el formato de fecha ISO
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

class UserManager:
    """Gestiona información de usuarios del bot usando PostgreSQL"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_user(self, username: str) -> Optional[UserInfo]:
        """Obtiene un usuario de la tabla users por telegram_username."""
        try:
            with self.db_manager.get_connection() as (conn, cursor):
                username_clean = username.lstrip('@')  # Remover @ si existe
                cursor.execute(
                    "SELECT telegram_username, session_id, name, email, message_count, created_at FROM users WHERE telegram_username = %s;",
                    (username_clean,)
                )
                row = cursor.fetchone()
                if row:
                    return UserInfo(
                        telegram_username=row[0],
                        session_id=row[1],
                        name=row[2],
                        email=row[3],
                        message_count=row[4] if row[4] is not None else 0,
                        created_at=row[5]
                    )
                return None
        except Exception as e:
            print(f"Error al obtener usuario {username}: {e}")
            return None

    def increment_message_count(self, username: str):
        """Incrementa el contador de mensajes de un usuario."""
        try:
            with self.db_manager.get_connection() as (conn, cursor):
                username_clean = username.lstrip('@')
                cursor.execute(
                    "UPDATE users SET message_count = COALESCE(message_count, 0) + 1 WHERE telegram_username = %s;",
                    (username_clean,)
                )
                conn.commit()
        except Exception as e:
            print(f"Error al incrementar contador de mensajes para el usuario {username}: {e}")
            raise
