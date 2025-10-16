# Arquitectura detallada

Esta aplicación es una API web que expone endpoints para conversar con SAÚ. Por dentro, separa claramente la capa web, la lógica de negocio (BotCore), y el motor RAG (OpenAI + Pinecone), además de módulos de persistencia.

## Componentes principales
- Servidor web (Flask): `src/web_handler.py` expone los endpoints y valida solicitudes.
- Núcleo conversacional: `src/bot_core.py` orquesta usuarios, sesiones y el modelo.
- Motor RAG: `src/RAG_ChatBot.py` realiza búsqueda semántica y genera respuestas con OpenAI.
- Persistencia: `src/database_manager.py`, `src/user_manager.py`, `src/session_manager.py`.
- Arranque: `run_web_bot.py` (lee entorno, valida dependencias, inicia servicios y servidor).
- Despliegue: Railway usando `Procfile` y `railway.json`.

## Flujo extremo a extremo (E2E)
1) El frontend envía `POST /api/chat` con `{ name, message }`.
2) Flask valida que existan los campos requeridos y construye un objeto de entrada con metadatos (IP, user-agent).
3) `BotCore` busca el usuario por `name` en la tabla `users` y recupera el contexto reciente de la sesión.
4) `BotCore` compone una "pregunta enriquecida" (mensaje + contexto) y llama a `SauAI` usando el `name` del usuario.
5) `SauAI` usa el retriever (Pinecone) para traer fragmentos relevantes y luego el modelo de OpenAI genera la respuesta.
6) La API devuelve una respuesta JSON con el contenido y metadatos útiles (p. ej., `session_id`).

## Responsabilidades y límites
- Web (Flask): validación básica, CORS, serialización JSON, códigos de estado.
- BotCore: reglas de negocio de conversación (qué contexto incluir, cómo responder ante errores temporales, etc.).
- RAG: recuperar y generar texto consistente con la especialidad (vida saludable).
- Persistencia: almacenar información mínima necesaria para personalizar y dar continuidad.

## Decisiones de diseño
- Separación fuerte entre capa web y lógica: facilita probar, mantener y eventualmente cambiar el framework web.
- RAG desacoplado: cambiar embeddings, índice o LLM no afecta la API ni el BotCore.
- CORS explícito: solo dominios permitidos pueden consumir la API.
- Variables de entorno: claves y conexiones no están hardcodeadas.

## Escalabilidad y operación
- Escala horizontal en Railway levantando más instancias si es necesario.
- El estado de conversación reciente es corto; la base de datos permite extenderlo.
- Health check (`/api/health`) para monitoreo y diagnósticos.
