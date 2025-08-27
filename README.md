# SAÚ - Asistente de Vida Saludable 🧑‍⚕️

SAÚ es un chatbot inteligente especializado en vida saludable que funciona a través de Telegram. Utiliza tecnología RAG (Retrieval-Augmented Generation) con OpenAI y Pinecone para brindar consejos personalizados sobre alimentación, ejercicio, descanso y bienestar general.

## ✨ Características Principales

### 🤖 Asistente Inteligente
- **Especialización**: Enfocado exclusivamente en vida saludable
- **Personalización**: Adapta sus respuestas según la edad, necesidades y limitaciones del usuario
- **Conversacional**: Interacción natural y amigable
- **Memoria**: Recuerda conversaciones anteriores y contexto del usuario

## 🛠️ Instalación

### Requisitos Previos
- Python 3.8+
- Cuenta de OpenAI con API key
- Cuenta de Pinecone con API key
- Bot de Telegram creado con @BotFather

### 1. Clonar el Repositorio
```bash
git clone <tu-repositorio>
cd Simple-RAG-Chatbot
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno
Crear archivo `.env` con:
```env
OPENAI_API_KEY=tu_openai_api_key
PINECONE_API_KEY=tu_pinecone_api_key
TELEGRAM_BOT_TOKEN=tu_telegram_bot_token
```

### 4. Preparar Base de Conocimientos
```bash
python src/context_upload.py
```

### 5. Ejecutar el Bot
```bash
python run_telegram_bot.py
```

## 📁 Estructura del Proyecto

```
Simple-RAG-Chatbot/
├── src/
│   ├── RAG_ChatBot.py           # Lógica principal del chatbot
│   ├── telegram_bot.py          # Integración con Telegram
│   ├── session_manager.py       # Gestión de sesiones de usuario
│   ├── user_manager.py          # Gestión de información de usuarios
│   └── context_upload.py        # Carga de contexto a Pinecone
├── run_telegram_bot.py          # Script principal
├── requirements.txt            # Dependencias
├── user_sessions.json          # Datos de sesiones
└── README.md                   # Esta documentación
```

## 🎯 Uso del Bot

### Comandos Básicos
- **Iniciar conversación**: Simplemente envía cualquier mensaje

### Ejemplos de Interacción

#### Solicitar Consejos de Salud:
```
Usuario: "Quiero hacer ejercicio para ganar músculo"
SAÚ: "¡Perfecto! Para darte una rutina personalizada, ¿me puedes contar cuántos años tienes y qué experiencia tienes en entrenamiento?"
```

## 🔧 Funcionalidades Técnicas

### Gestión de Sesiones
- **Persistencia**: Guardado automático de conversaciones
- **Contexto**: Memoria de conversaciones previas
- **Personalización**: Almacenamiento de preferencias y datos del usuario

### Integración RAG
- **Vector Store**: Pinecone para almacenamiento de embeddings
- **Retrieval**: Búsqueda semántica de información relevante
- **Generation**: Respuestas contextualizadas con OpenAI GPT-4

## 🚀 Características Avanzadas

### Personalización
- Adapta respuestas según edad del usuario
- Considera limitaciones físicas y condiciones de salud
- Recuerda objetivos y preferencias personales

### Seguridad
- No proporciona diagnósticos médicos
- Redirige a profesionales cuando es necesario
- Manejo seguro de datos de usuario

### Escalabilidad
- Procesamiento concurrente de mensajes
- Gestión eficiente de múltiples usuarios
- Sistema robusto de manejo de errores

## 📞 Soporte

Para reportar problemas o solicitar funciones:
1. Revisa los logs en `telegram_bot.log`
2. Verifica la configuración de las APIs

---

**Desarrollado por ADPIAR Technologies** 🚀
