# SAÚ AI - API Web de Vida Saludable

SAÚ es un asistente especializado en vida saludable expuesto como una API web. Usa RAG (Retrieval-Augmented Generation) con OpenAI y Pinecone para responder con contexto sobre alimentación, ejercicio, descanso y hábitos saludables.

- Demo API (health): `GET /api/health`
- Uso principal: `POST /api/chat`
- Documentación ampliada: carpeta `docs/`

## ✨ Características
- Especialización en vida saludable (no temas generales)
- Respuestas personalizadas con memoria corta de conversación
- Motor RAG (OpenAI + Pinecone) para respuestas con contexto
- API web simple de integrar desde cualquier frontend
- Lista para desplegar en Railway

## 🚀 Quick Start (local)
1) Requisitos
- Python 3.9+
- Cuenta de OpenAI (API key)
- Cuenta de Pinecone (API key)
- PostgreSQL (URL de conexión)

2) Instalar dependencias
```bash
pip install -r requirements.txt
```

3) Variables de entorno (`.env`)
```env
OPENAI_API_KEY=tu_openai_api_key
PINECONE_API_KEY=tu_pinecone_api_key
DATABASE_URL=postgresql://user:pass@host:5432/db
```

4) Preparar el índice (opcional si ya existe)
```bash
python src/context_upload.py
```

5) Ejecutar el servidor
```bash
python run_web_bot.py
```

## ⚙️ Variables de Entorno
- `OPENAI_API_KEY`: clave de OpenAI para embeddings y chat
- `PINECONE_API_KEY`: clave de Pinecone para el vector store
- `DATABASE_URL`: conexión a PostgreSQL
- `PORT`: asignado por Railway (no lo configures localmente)
- `HOST`: por defecto `0.0.0.0` (no es necesario definirla)

## 🌐 API (resumen)
Endpoints principales (ver detalles y ejemplos en `docs/api.md`):
- `GET /api/health`: estado del servicio
- `POST /api/chat`: enviar `{ username, message }` y recibir respuesta de SAÚ
- `POST /api/check-user`: generar/verificar `@username` desde email (para clientes web)
- `POST /api/typing` (opcional): simular "escribiendo" para UX

Headers recomendados:
- `Content-Type: application/json`
- `Accept: application/json`

## 🔐 CORS
Permitidos por defecto (ver `src/web_handler.py`):
- `https://gamersmed.apversus.com` (producción)
- `https://apv-web-git-dev-adpiars-projects.vercel.app` (desarrollo)
- `http://localhost:3000` (local)

Ajusta la lista de orígenes según tus dominios.

## 🏗️ Arquitectura (resumen)
- API web: Flask (`src/web_handler.py`)
- Núcleo de negocio: `BotCore` (`src/bot_core.py`)
- Motor RAG: `SauAI` (`src/RAG_ChatBot.py`) con OpenAI + Pinecone
- Persistencia: `database_manager.py`, `user_manager.py`, `session_manager.py`
- Arranque: `run_web_bot.py`
- Despliegue: `Procfile`, `railway.json`

Más detalles en `docs/architecture.md`.

## ☁️ Despliegue en Railway
1) Asegúrate de tener:
- `Procfile` con `web: python run_web_bot.py`
- `railway.json` con `startCommand` y `healthcheckPath: /api/health`
- `requirements.txt` con `flask` y `flask-cors`

2) Configura variables en Railway:
- `OPENAI_API_KEY`, `PINECONE_API_KEY`, `DATABASE_URL`

3) Haz push a `main`. Railway instalará dependencias y arrancará.

4) Verifica:
- Logs de arranque: puerto, host, variables clave
- `GET /api/health` → 200 con JSON esperado

Guía completa y troubleshooting: `docs/deployment.md` y `docs/operations.md`.

## 🧠 Cómo responde SAÚ
- `BotCore` toma datos de usuario + contexto reciente y enriquece la pregunta
- `SauAI` recupera fragmentos relevantes en Pinecone y llama al LLM de OpenAI
- La API devuelve un JSON con `content`, `response_type` y metadatos

Detalles: `docs/botcore.md` y `docs/rag.md`.

## 🗄️ Datos y Sesiones
- `UserManager`: nombre, edad, objetivos (si están disponibles)
- `SessionManager`: últimas N interacciones para continuidad
- Estrategias de username/sesiones y expiración: `docs/users_sessions.md`

## 📁 Estructura del Proyecto
```
sau-bot/
├── src/
│   ├── RAG_ChatBot.py
│   ├── web_handler.py
│   ├── bot_core.py
│   ├── session_manager.py
│   ├── user_manager.py
│   ├── database_manager.py
│   └── context_upload.py
├── docs/
│   ├── index.md
│   ├── api.md
│   ├── architecture.md
│   ├── botcore.md
│   ├── rag.md
│   ├── database.md
│   ├── users_sessions.md
│   ├── deployment.md
│   └── operations.md
├── run_web_bot.py
├── requirements.txt
├── Procfile
├── railway.json
└── README.md
```

## 🛟 Troubleshooting rápido
- 502 Bad Gateway en Railway: verifica `0.0.0.0` y uso de `PORT` de entorno
- `No module named 'flask'`: añade a `requirements.txt` y redeploy
- Índice de Pinecone no existe: ejecuta `python src/context_upload.py`
- Latencia alta: baja `k` del retriever o reduce tamaño de fragmentos

Runbooks y verificación: `docs/operations.md`.

## 📞 Soporte
- Revisa logs de arranque y `GET /api/health`
- Consulta las guías en `docs/`

---

Desarrollado por ADPIAR Technologies 🚀
