# Usuarios y Sesiones (detallado)

## Estrategia de `username`
- Debe ser estable por usuario (ej. `@` + parte local del email).
- Evita colisiones: si hay duplicados, agrega sufijos controlados.

## Sesiones (`session_id`)
- Identifica una conversación continua (por ejemplo, por pestaña o visita).
- El frontend puede conservar el `session_id` para continuidad.

## Expiración y tamaño de contexto
- Guarda solo los últimos N mensajes (p. ej., 5) para mantener rapidez.
- Expira sesiones inactivas (p. ej., >14 días) para limpiar datos.

## Ejemplo de ciclo
1. `check-user` genera `@username` si no existe.
2. El frontend crea/recupera `session_id`.
3. Envía mensajes con ese `username` y `session_id` asociados.
4. El backend personaliza y mantiene continuidad con el contexto reciente.
