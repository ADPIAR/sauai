# Documentación de SAÚ AI (API Web)

Esta carpeta explica de forma clara cómo funciona cada parte del proyecto.

## Mapa del sistema
- API (Flask): recibe peticiones y devuelve respuestas JSON.
- BotCore: decide qué contexto usar y consulta al modelo.
- RAG (OpenAI + Pinecone): busca info relevante y genera la respuesta.
- BD (PostgreSQL): guarda datos de usuario y contexto breve.
- Despliegue (Railway): ejecuta el servidor y lo expone a Internet.

## Guías por tema
- Arquitectura: `architecture.md`
- API (endpoints): `api.md`
- Núcleo conversacional: `botcore.md`
- RAG (OpenAI + Pinecone): `rag.md`
- Base de datos: `database.md`
- Usuarios y sesiones: `users_sessions.md`
- Despliegue: `deployment.md`
- Operación y monitoreo: `operations.md`

## Preguntas frecuentes (FAQ)
- ¿Necesito configurar `PORT`? No, Railway lo asigna.
- ¿Qué dominios pueden llamar la API? Ver CORS en `api.md`.
- ¿Cómo personaliza respuestas? Con datos de usuario y contexto reciente.
- ¿Qué hago si el health check falla? Ver runbook en `operations.md`.
