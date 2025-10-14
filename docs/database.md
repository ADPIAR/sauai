# Base de Datos y Persistencia (detallado)

La base usa PostgreSQL para guardar información mínima pero útil.

## Entidades (conceptual)
- Usuario
  - `username` (clave), `personal_name`, `age`, `user_needs`
- Sesión
  - `session_id` (UUID), `username`, `messages[]` recientes, `updated_at`

Nota: La implementación exacta puede variar; el objetivo es mantener suficiente información para personalizar y continuar conversaciones.

## Relaciones
- Un Usuario puede tener múltiples Sesiones.
- Cada Sesión guarda un resumen corto de las últimas interacciones.

## Ciclo de vida
- Al recibir un mensaje, se recupera/crea usuario y sesión.
- Se añade el intercambio (usuario → bot) a la sesión.

## Migraciones
- El código actual crea/verifica tablas al iniciar.
- Para entornos más exigentes, considera herramientas de migraciones (ej. Alembic).
