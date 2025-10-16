# API Web (detallada)

Esta sección cubre los endpoints, cómo llamarlos desde tu frontend, errores comunes y consideraciones de seguridad/CORS.

## Autenticación
Actualmente no requiere autenticación. Si necesitas auth (tokens/JWT), puede añadirse como middleware en Flask.

## CORS
Permitidos:
- https://gamersmed.apversus.com
- https://apv-web-git-dev-adpiars-projects.vercel.app
- http://localhost:3000

Si necesitas añadir dominios, actualiza `CORS(self.app, origins=[...])` en `src/web_handler.py`.

## Headers recomendados
- `Content-Type: application/json`
- `Accept: application/json`

## Endpoints

### GET /api/health
Verifica que el servicio esté activo y listo.

Respuesta 200:
```json
{
  "status": "healthy",
  "message": "SAÚ AI Backend is running",
  "service": "SAÚ AI Web API",
  "version": "1.0.0",
  "endpoints": {"chat":"/api/chat","check_user":"/api/check-user","typing":"/api/typing"}
}
```

### POST /api/chat
Envía un mensaje a SAÚ para obtener una respuesta.

Request:
```http
POST /api/chat HTTP/1.1
Content-Type: application/json

{
  "name": "Julian",
  "message": "Hola, ¿cómo estás?",
  "metadata": {
    "client": "web",
    "page": "/chat"
  }
}
```

Respuesta 200:
```json
{
  "success": true,
  "response": {
    "content": "¡Hola! Soy SAÚ...",
    "response_type": "text",
    "metadata": {
      "session_id": "uuid",
      "timestamp": "2025-01-01T12:00:00Z"
    }
  }
}
```

Errores:
- 400 si falta `name` o `message`.
- 500 si hay error interno (p. ej., redes, LLM, Pinecone).

Buenas prácticas:
- Usa un `name` que exista en la tabla `users` de la base de datos.
- Maneja estados de "escribiendo" con `/api/typing` si lo deseas.

### POST /api/check-user
Verifica si un usuario existe en la base de datos por su `name`.

Request:
```json
{ "name": "Julian" }
```

Respuesta 200:
```json
{ "success": true, "exists": true, "message": "Usuario encontrado" }
```

### POST /api/typing (opcional)
Simula indicador de "escribiendo" para UX.

Request:
```json
{ "duration": 3 }
```

Respuesta 200:
```json
{ "success": true, "response": { "response_type": "typing", "metadata": { "duration": 3 } } }
```

## Límites y rendimiento
- Las respuestas dependen de latencia de OpenAI y Pinecone (normalmente 0.5–3s).
- Considera añadir timeouts y reintentos en el frontend.

## Seguridad
- No exponer claves en el cliente; las usa el servidor desde variables de entorno.
- Si agregas auth, valida tokens en cada request.
