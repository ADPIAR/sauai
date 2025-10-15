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
                    "SELECT telegram_username, session_id, name, email, created_at FROM users WHERE telegram_username = %s;",
                    (username_clean,)
                )
                row = cursor.fetchone()
                if row:
                    return UserInfo(
                        telegram_username=row[0],
                        session_id=row[1],
                        name=row[2],
                        email=row[3],
                        created_at=row[4]
                    )
                return None
        except Exception as e:
            print(f"Error al obtener usuario {username}: {e}")
            return None
