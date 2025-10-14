# Operación y Monitoreo (runbooks)

## Verificar estado
1. Revisar logs de arranque (puerto/host/variables).
2. `GET /api/health` debe devolver 200 y JSON esperado.
3. Probar `POST /api/chat` con un mensaje simple.

## Runbook: health check falla
- Confirmar que el proceso está corriendo en Railway.
- Verificar `flask` y `flask-cors` instalados.
- Revisar que se use `host='0.0.0.0'` y `port=os.getenv('PORT')`.

## Runbook: latencia alta
- Reducir `k` de retrieval (p. ej., 3 → 2).
- Fragmentar documentos más pequeños en el índice.
- Activar indicadores de "typing" en frontend para mejor UX.

## Runbook: errores de API
- Revisar `OPENAI_API_KEY` y `PINECONE_API_KEY`.
- Verificar que el índice Pinecone existe.
- Inspeccionar trazas de error en logs.

## Observabilidad adicional (opcional)
- Añadir IDs de correlación por request.
- Métricas de tiempo de respuesta por endpoint.
- Alertas si health check falla X veces seguidas.
