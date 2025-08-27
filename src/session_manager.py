#!/usr/bin/env python3
"""
Gestor de sesiones y memoria por usuario - SIMPLIFICADO
"""

import uuid
import threading
import logging
import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from database_manager import DatabaseManager # Importa DatabaseManager
import json # Añadir esta línea

# Usar el logger configurado en run_telegram_bot.py
logger = logging.getLogger(__name__)

@dataclass
class UserSession:
    """Información básica de sesión de un usuario"""
    session_id: uuid.UUID # Ahora es un UUID, no string
    user_id: int
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_activity: datetime.datetime = field(default_factory=datetime.datetime.now)
    user_preferences: Dict = field(default_factory=dict)
    
    # Nota: first_name, last_name, username, personal_name, age, user_needs
    # ahora se gestionan en UserManager y UserInfo. Aquí solo el ID de usuario.

class SessionManager:
    """Gestiona sesiones y memoria por usuario usando PostgreSQL"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._lock = threading.Lock()
        logger.info("🔧 Inicializando SessionManager con DatabaseManager")
        # No es necesario cargar sesiones aquí, se obtienen/crean on-demand
        logger.info("✅ SessionManager inicializado")
    
    def get_or_create_session(self, user_id: int) -> UserSession:
        """Obtiene sesión existente o crea una nueva para el usuario."""
        with self._lock:
            try:
                # Intentar obtener la sesión más reciente del usuario
                self.db_manager.cursor.execute(
                    "SELECT session_id, user_id, created_at, last_activity, user_preferences FROM sessions WHERE user_id = %s ORDER BY last_activity DESC LIMIT 1;",
                    (user_id,)
                )
                row = self.db_manager.cursor.fetchone()
                
                if row:
                    # Sesión existente, actualizar last_activity
                    session = UserSession(
                        session_id=row[0],
                        user_id=row[1],
                        created_at=row[2],
                        last_activity=row[3],
                        user_preferences=row[4] if row[4] else {}
                    )
                    self.db_manager.cursor.execute(
                        "UPDATE sessions SET last_activity = %s WHERE session_id = %s;",
                        (datetime.datetime.now(), session.session_id)
                    )
                    self.db_manager.conn.commit()
                    logger.info(f"👤 Actualizando sesión existente {session.session_id} para usuario {user_id}")
                    return session
                else:
                    # Crear nueva sesión
                    new_session_id = uuid.uuid4() # Generar UUID en Python para la inserción
                    self.db_manager.cursor.execute(
                        "INSERT INTO sessions (session_id, user_id, created_at, last_activity) VALUES (%s, %s, %s, %s) RETURNING session_id, user_id, created_at, last_activity, user_preferences;",
                        (str(new_session_id), user_id, datetime.datetime.now(), datetime.datetime.now())
                    )
                    self.db_manager.conn.commit()
                    new_session_row = self.db_manager.cursor.fetchone()
                    if new_session_row:
                        session = UserSession(
                            session_id=new_session_row[0],
                            user_id=new_session_row[1],
                            created_at=new_session_row[2],
                            last_activity=new_session_row[3],
                            user_preferences=new_session_row[4] if new_session_row[4] else {}
                        )
                        logger.info(f"🆕 Creando nueva sesión {session.session_id} para usuario {user_id}")
                        return session
                    else:
                        raise Exception("No se pudo crear la sesión o recuperar sus datos.")
            except Exception as e:
                self.db_manager.conn.rollback()
                logger.error(f"❌ Error en get_or_create_session para usuario {user_id}: {e}")
                raise

    def add_message_to_history(self, session_id: uuid.UUID, message: str, is_user: bool = True):
        """Añade mensaje al historial de conversación de una sesión."""
        with self._lock:
            try:
                logger.info(f"💬 Guardando mensaje en sesión {session_id} de {'usuario' if is_user else 'bot'}: {message[:50]}...")
                self.db_manager.cursor.execute(
                    "INSERT INTO conversation_messages (session_id, timestamp, message, is_user) VALUES (%s, %s, %s, %s);",
                    (str(session_id), datetime.datetime.now(), message, is_user)
                )
                self.db_manager.conn.commit()
            except Exception as e:
                self.db_manager.conn.rollback()
                logger.error(f"❌ Error al guardar mensaje en sesión {session_id}: {e}")
                raise

    def get_conversation_context(self, session_id: uuid.UUID, limit: int = 10) -> str:
        """Obtiene contexto de conversación reciente para una sesión."""
        with self._lock:
            try:
                self.db_manager.cursor.execute(
                    "SELECT message, is_user FROM conversation_messages WHERE session_id = %s ORDER BY timestamp DESC LIMIT %s;",
                    (str(session_id), limit)
                )
                rows = self.db_manager.cursor.fetchall()
                context = []
                for msg, is_user in reversed(rows): # Invertir para orden cronológico
                    role = "Usuario" if is_user else "SAÚ"
                    context.append(f"{role}: {msg}")
                return "\n".join(context)
            except Exception as e:
                logger.error(f"❌ Error al obtener contexto de conversación para sesión {session_id}: {e}")
                return ""

    def update_session_preferences(self, session_id: uuid.UUID, preferences: Dict):
        """Actualiza las preferencias JSONB de una sesión."""
        with self._lock:
            try:
                # psycopg2 requiere que los JSONB se pasen como cadenas JSON
                json_pref = json.dumps(preferences) # Convertir dict a string JSON
                self.db_manager.cursor.execute(
                    "UPDATE sessions SET user_preferences = user_preferences || %s::jsonb WHERE session_id = %s;",
                    (json_pref, str(session_id))
                )
                self.db_manager.conn.commit()
                logger.info(f"✅ Preferencias de sesión {session_id} actualizadas.")
            except Exception as e:
                self.db_manager.conn.rollback()
                logger.error(f"❌ Error al actualizar preferencias de sesión {session_id}: {e}")
                raise

# Eliminar la línea duplicada o asegurar que solo haya una instancia de SessionManager si no se usa como singleton.
# Si esta línea es para compatibilidad con código antiguo, se debería revisar la arquitectura.
# SessionManager = SessionManager 