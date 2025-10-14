# Núcleo Conversacional (BotCore) - Detallado

`BotCore` es el orquestador de la conversación. Separa la lógica de negocio de la capa web.

## Qué hace
- Enriquecer el mensaje del usuario con contexto útil.
- Consultar datos del usuario y conversación reciente.
- Delegar la generación al motor RAG (`SauAI`).
- Manejar errores y devolver respuestas consistentes.

## Flujo detallado
1. Llega `{ username, message }` desde la API.
2. `UserManager` aporta datos: nombre, edad, objetivos (si existen).
3. `SessionManager` aporta últimos mensajes (p. ej., 5 recientes).
4. Se construye `enhanced_question` con ese contexto.
5. Se llama `SauAI.ask(enhanced_question)`.
6. Se retorna una respuesta en formato estable: `content`, `response_type`, `metadata`.

## Pseudocódigo simplificado
```text
function process_message(input):
  user = user_manager.get_user(input.username)
  recent = session_manager.get_recent(input.session_id, limit=5)
  context = build_context(user, recent)
  question = enrich(input.message, context)
  try:
    answer = sau_ai.ask(question)
    session_manager.append(input.session_id, input.message, answer)
    return { content: answer, response_type: "text" }
  except TemporaryError:
    return { content: "Estoy teniendo un problema momentáneo, intenta de nuevo.", response_type: "text" }
  except Exception:
    return { content: "Ocurrió un error inesperado.", response_type: "text" }
```

## Manejo de errores
- Reintentos ante fallos transitorios (red, timeouts) con espera corta.
- Logging estructurado para diagnósticos.
- Mensajes seguros y breves al usuario final.

## Buenas prácticas
- Limitar la cantidad de contexto para mantener latencia baja.
- Registrar solo lo necesario para mejorar el servicio (privacidad).
- Usar IDs de sesión estables por usuario/conversación.
