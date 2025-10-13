Contexto del Proyecto
Tengo un chatbot especializado en vida saludable (SAÚ AI) que actualmente funciona exclusivamente en Telegram, desplegado en Railway. El bot tiene las siguientes características:

Arquitectura actual:

El bot utiliza un sistema de identificación basado en @username de Telegram (requiere registro previo en web)
Cada usuario se registra automáticamente la primera vez que interactúa con el bot
El bot maneja sesiones/conversaciones basándose en el @username como identificador único
Almacena historial de mensajes categorizados por sesión (UUID) asociada a cada usuario
Utiliza un sistema RAG (Retrieval Augmented Generation) con Pinecone y OpenAI
Toda la lógica del bot está acoplada a la API de Telegram (telegram_bot.py)
El sistema incluye gestión de usuarios (UserManager), sesiones (SessionManager) y base de datos (DatabaseManager)

Flujo actual:

Usuario inicia conversación con el bot en Telegram
Bot crea/actualiza automáticamente el registro del usuario en la base de datos
Bot obtiene o crea una sesión para el usuario basada en su @username
Bot procesa el mensaje usando SAÚ AI (RAG + contexto de conversación)
Bot responde y guarda tanto el mensaje del usuario como su respuesta en el historial

Objetivo de la Modificación
Necesito que el mismo bot funcione tanto en Telegram como en nuestra página web, manteniendo una experiencia unificada. Los usuarios deberían poder:

Continuar la misma conversación desde cualquier plataforma usando su @username como identificador
Ver el mismo historial de conversación sin importar desde dónde accedan
Recibir respuestas consistentes del bot SAÚ AI con el mismo contexto y personalización
Mantener sus datos de usuario (nombre personal, edad, necesidades) sincronizados entre plataformas

Tarea Principal
Refactorizar la arquitectura del bot para desacoplar la lógica de negocio de la plataforma Telegram, de manera que:

Separar la lógica central del bot (SAÚ AI + gestión de sesiones) de los handlers específicos de Telegram
Crear una capa de abstracción que pueda recibir mensajes desde cualquier fuente (Telegram, Web, futuras plataformas)
Mantener la identificación de usuarios basada en el @username pero permitiendo que el mensaje venga desde diferentes orígenes
Preservar toda la funcionalidad actual: RAG, contexto de conversación, personalización de usuario, y gestión de sesiones

Cambios Específicos Necesarios
1. Abstracción de la entrada de mensajes:

Actualmente el bot recibe objetos de tipo "Update" de Telegram en telegram_bot.py
Necesitamos que la lógica principal reciba un formato genérico como: {origen: "telegram/web", username: "@usuario", mensaje: "texto", metadata: {}}
La función _process_message_async() debe ser reemplazada por una función genérica que no dependa de Telegram

2. Gestión de sesiones unificada:

Actualmente las sesiones se identifican por @username y se almacenan en la tabla 'sessions' con UUID
El sistema ya está preparado para esto, solo necesitamos asegurar que funcione igual desde web
Un usuario @juanperez debe tener la misma sesión/historial ya sea que escriba desde Telegram o desde la web

3. Abstracción de las respuestas:

Actualmente el bot responde usando métodos específicos de Telegram (reply_text, reply_chat_action, etc.)
Necesitamos que la lógica retorne respuestas en formato genérico que luego se adapten según la plataforma
Por ejemplo: retornar {tipo: "texto", contenido: "mensaje", metadata: {}} o {tipo: "typing", duracion: 3}

4. Manejo del contexto y estado:

El bot ya mantiene contexto usando SessionManager.get_conversation_context() y UserManager
Solo necesitamos asegurar que esta funcionalidad sea accesible desde cualquier plataforma
El contexto incluye: historial de conversación, datos del usuario (nombre, edad, necesidades), y preferencias

5. Compatibilidad hacia atrás:

Los usuarios actuales de Telegram deben seguir funcionando exactamente igual
No debe haber interrupción del servicio actual
La refactorización debe ser transparente para el usuario final

Estructura Sugerida (Basada en el código actual)
El bot debería organizarse en capas, aprovechando la arquitectura existente:

Capa de Entrada (Platform Adapters):

Telegram Handler: Refactorizar telegram_bot.py para usar la nueva capa central
Web Handler: Nuevo módulo que reciba mensajes HTTP y los convierta al formato interno
Ambos deben llamar a la misma función central: procesar_mensaje(username, mensaje, origen)

Capa de Lógica (Core Bot) - NUEVA:

Crear bot_core.py que contenga:
- Función procesar_mensaje() que reemplace _process_message_async()
- Integración con SauAI (RAG_ChatBot.py)
- Uso de UserManager y SessionManager existentes
- Retorno de respuestas en formato genérico

Capa de Salida (Response Adapters):

Telegram Responder: Adaptar las respuestas genéricas a métodos de Telegram
Web Responder: Convertir respuestas genéricas a JSON para la API web

Componentes existentes a preservar:
- DatabaseManager (PostgreSQL con pool de conexiones)
- UserManager (gestión de usuarios con @username)
- SessionManager (sesiones con UUID y historial)
- SauAI (RAG con Pinecone y OpenAI)

Consideraciones Importantes

Validación de usuarios: El sistema actual ya registra automáticamente usuarios con @username, esto debe mantenerse
Historial unificado: Los mensajes ya se guardan en conversation_messages con session_id, solo necesitamos agregar campo 'origen'
Funcionalidades específicas de plataforma: 
- Telegram: typing indicators, reply_text, reply_chat_action
- Web: JSON responses, HTTP status codes, CORS headers
- Identificar qué features son exclusivas y cómo adaptarlas
Testing: Crear tests unitarios para bot_core.py que no dependan de Telegram
Logs y debugging: Agregar información sobre el origen de cada mensaje en los logs existentes
Base de datos: Considerar agregar campo 'origen' a conversation_messages para tracking
Manejo de errores: Mantener el sistema robusto de reintentos y timeouts existente

Resultado Esperado
Al final de esta refactorización, deberíamos poder:

Llamar a una función como procesar_mensaje(username, mensaje, origen) desde cualquier parte
Obtener una respuesta genérica que pueda ser formateada para cualquier plataforma
Mantener toda la funcionalidad actual del bot en Telegram (RAG, contexto, personalización)
Estar listos para agregar fácilmente un endpoint HTTP que reciba mensajes desde la web
Preservar el sistema de logging, manejo de errores y reintentos existente

Plan de Implementación Detallado:

Fase 1: Crear bot_core.py
- Extraer la lógica de _process_message_async() a una función independiente
- Crear interfaz genérica para entrada y salida de mensajes
- Mantener integración con UserManager, SessionManager y SauAI

Fase 2: Refactorizar telegram_bot.py
- Modificar para usar bot_core.py en lugar de lógica interna
- Adaptar respuestas genéricas a métodos de Telegram
- Probar que todo funciona igual que antes

Fase 3: Preparar para web (futuro)
- Crear web_handler.py que use bot_core.py
- Implementar endpoint HTTP básico
- Adaptar respuestas genéricas a JSON

Detalles Técnicos Específicos (Basados en el código actual):

Estructura de Base de Datos existente:
- users_telegram: username (PK), telegram_user_id, first_name, last_name, personal_name, age, user_needs, etc.
- sessions: session_id (UUID), username (FK), created_at, last_activity, user_preferences (JSONB)
- conversation_messages: message_id (UUID), session_id (FK), timestamp, message, is_user

Componentes clave a preservar:
- DatabaseManager: Pool de conexiones PostgreSQL con reconexión automática
- UserManager: Gestión automática de usuarios con @username como identificador
- SessionManager: Sesiones con UUID, historial de conversación, preferencias JSONB
- SauAI: RAG con Pinecone (índice "sauai"), OpenAI GPT-5-mini, embeddings text-embedding-3-large

Flujo actual en telegram_bot.py:
1. handle_message() → _process_message_async()
2. _safe_user_operation() → UserManager.create_or_update_user()
3. _safe_session_operation() → SessionManager.get_or_create_session()
4. _safe_add_message() → SessionManager.add_message_to_history()
5. _safe_process_with_sauai() → SauAI.ask() con contexto
6. _send_response() → reply_text()

Cambios mínimos necesarios:
- Crear bot_core.py con función procesar_mensaje(username, mensaje, origen)
- Modificar telegram_bot.py para usar bot_core.py
- Agregar campo 'origen' a conversation_messages (opcional)
- Mantener toda la lógica de reintentos, timeouts y manejo de errores

IMPORTANTE: No necesito que implementes la interfaz web ni el endpoint HTTP todavía. Solo necesito que la lógica del bot esté lista para recibirlos. Primero hagamos esta separación de capas, probemos que Telegram sigue funcionando igual, y luego agregamos la capa web.