# Arquitectura Refactorizada - SAÚ AI Bot

## Resumen de Cambios

Se ha refactorizado exitosamente el bot SAÚ AI para desacoplar la lógica de negocio de la plataforma específica (Telegram). Ahora el bot puede funcionar tanto en Telegram como en web manteniendo la misma funcionalidad.

## Estructura de la Nueva Arquitectura

### 1. BotCore (`src/bot_core.py`)
**Lógica central desacoplada** que contiene toda la funcionalidad del bot:

- **Clase `BotCore`**: Maneja el procesamiento de mensajes independientemente de la plataforma
- **Clase `MessageInput`**: Formato genérico para entrada de mensajes
- **Clase `MessageResponse`**: Formato genérico para respuestas
- **Función `process_message_async()`**: Función de conveniencia para uso directo

### 2. Telegram Handler (`src/telegram_bot.py`)
**Adaptador para Telegram** que usa BotCore:

- Mantiene toda la funcionalidad original de Telegram
- Usa BotCore para el procesamiento de mensajes
- Adapta respuestas genéricas a métodos específicos de Telegram
- **100% compatible hacia atrás** - los usuarios no notan ningún cambio

### 3. Web Handler (`src/web_handler.py`)
**Ejemplo de integración web** que demuestra cómo usar BotCore:

- API REST con endpoints `/api/chat`, `/api/health`, `/api/typing`
- Manejo de CORS para integración frontend
- Mismo procesamiento de mensajes que Telegram
- Formato JSON para respuestas

## Flujo de Procesamiento

### Antes (Acoplado a Telegram)
```
Usuario → Telegram API → telegram_bot.py → Lógica específica → Respuesta Telegram
```

### Ahora (Desacoplado)
```
Usuario → Plataforma (Telegram/Web) → Adaptador → BotCore → Respuesta genérica → Adaptador → Usuario
```

## Componentes Preservados

Todos los componentes existentes se mantienen intactos:

- ✅ **DatabaseManager**: Pool de conexiones PostgreSQL
- ✅ **UserManager**: Gestión de usuarios con @username
- ✅ **SessionManager**: Sesiones con UUID y historial
- ✅ **SauAI**: RAG con Pinecone y OpenAI
- ✅ **Funcionalidad completa**: RAG, contexto, personalización, manejo de errores

## Formato de Mensajes Genérico

### Entrada (`MessageInput`)
```python
{
    "username": "@usuario",
    "message": "Hola, ¿cómo estás?",
    "origin": "telegram",  # o "web"
    "metadata": {
        "telegram_user_id": 123456,
        "first_name": "Juan",
        "last_name": "Pérez"
    }
}
```

### Salida (`MessageResponse`)
```python
{
    "content": "¡Hola Juan! Soy SAÚ...",
    "response_type": "text",  # "text", "typing", "error"
    "metadata": {
        "session_id": "uuid",
        "username": "@usuario",
        "origin": "telegram",
        "timestamp": "2024-01-01T12:00:00"
    }
}
```

## Uso de la Nueva Arquitectura

### Para Telegram (Sin cambios)
```python
# El código existente sigue funcionando igual
from src.telegram_bot import TelegramSauAI
from src.database_manager import DatabaseManager
from src.user_manager import UserManager
from src.session_manager import SessionManager

db_manager = DatabaseManager()
user_manager = UserManager(db_manager)
session_manager = SessionManager(db_manager)

bot = TelegramSauAI(user_manager, session_manager)
bot.run()
```

### Para Web (Nuevo)
```python
from src.web_handler import create_web_handler
from src.database_manager import DatabaseManager
from src.user_manager import UserManager
from src.session_manager import SessionManager

db_manager = DatabaseManager()
user_manager = UserManager(db_manager)
session_manager = SessionManager(db_manager)

web_handler = create_web_handler(user_manager, session_manager)
web_handler.run(host='0.0.0.0', port=5000)
```

### Uso Directo de BotCore
```python
from src.bot_core import BotCore, MessageInput, process_message_async

# Opción 1: Usar BotCore directamente
bot_core = BotCore(user_manager, session_manager)
message_input = MessageInput(
    username="@usuario",
    message="Hola",
    origin="custom_platform"
)
response = await bot_core.process_message(message_input)

# Opción 2: Usar función de conveniencia
response = await process_message_async(
    username="@usuario",
    message="Hola",
    origin="custom_platform",
    user_manager=user_manager,
    session_manager=session_manager
)
```

## Beneficios de la Refactorización

### 1. **Desacoplamiento**
- Lógica de negocio separada de la plataforma
- Fácil agregar nuevas plataformas (Discord, Slack, etc.)

### 2. **Reutilización**
- Mismo código para todas las plataformas
- Mantenimiento centralizado

### 3. **Compatibilidad**
- 100% compatible hacia atrás
- Usuarios de Telegram no notan cambios

### 4. **Escalabilidad**
- Fácil agregar nuevas funcionalidades
- Testing independiente de plataforma

### 5. **Flexibilidad**
- Respuestas adaptables a cada plataforma
- Metadata específica por origen

## Próximos Pasos

### Fase 1: ✅ Completada
- [x] Crear BotCore con lógica desacoplada
- [x] Refactorizar TelegramSauAI para usar BotCore
- [x] Verificar compatibilidad hacia atrás
- [x] Crear ejemplo de integración web

### Fase 2: Integración Web (Futuro)
- [ ] Implementar endpoint HTTP en producción
- [ ] Crear interfaz frontend
- [ ] Configurar CORS y seguridad
- [ ] Testing end-to-end

### Fase 3: Expansión (Futuro)
- [ ] Integración con Discord
- [ ] Integración con Slack
- [ ] API GraphQL
- [ ] Webhooks

## Testing

### Verificar Telegram
```bash
cd /Users/julian/Documents/dev/sau-bot
source venv/bin/activate
python run_telegram_bot.py
```

### Verificar Importaciones
```bash
cd /Users/julian/Documents/dev/sau-bot
source venv/bin/activate
python -c "from src.bot_core import BotCore, MessageInput, MessageResponse; print('✅ OK')"
```

## Archivos Modificados

1. **`src/bot_core.py`** - ✨ NUEVO: Lógica central desacoplada
2. **`src/telegram_bot.py`** - 🔄 MODIFICADO: Ahora usa BotCore
3. **`src/web_handler.py`** - ✨ NUEVO: Ejemplo de integración web
4. **`ARQUITECTURA_REFACTORIZADA.md`** - ✨ NUEVO: Esta documentación

## Archivos Sin Cambios

- `src/RAG_ChatBot.py` - Sin cambios
- `src/user_manager.py` - Sin cambios  
- `src/session_manager.py` - Sin cambios
- `src/database_manager.py` - Sin cambios
- `run_telegram_bot.py` - Sin cambios
- `requirements.txt` - Sin cambios

## Conclusión

La refactorización ha sido exitosa. El bot SAÚ AI ahora tiene una arquitectura desacoplada que:

- ✅ Mantiene 100% de la funcionalidad original
- ✅ Permite integración web fácil
- ✅ Facilita agregar nuevas plataformas
- ✅ Centraliza la lógica de negocio
- ✅ Preserva toda la personalización y contexto

El sistema está listo para recibir mensajes desde cualquier plataforma manteniendo la misma experiencia de usuario y funcionalidad completa del bot SAÚ AI.
