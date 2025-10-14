# Despliegue en Railway (paso a paso)

## 1) Preparar el repo
- `Procfile` con: `web: python run_web_bot.py`
- `railway.json` con `startCommand` y `healthcheckPath` (/api/health)
- `requirements.txt` con `flask` y `flask-cors`

## 2) Variables de entorno
Configura en Railway:
- `OPENAI_API_KEY`
- `PINECONE_API_KEY`
- `DATABASE_URL`

No configures `PORT`; Railway lo asigna.

## 3) Deploy
- Haz push a `main`.
- Railway detecta cambios, instala dependencias y arranca.

## 4) Verificación
- Logs deben mostrar: puerto, host y mensaje de arranque.
- Health check: `GET /api/health` debe devolver 200.

## Troubleshooting
- 502 Bad Gateway: verifica que el servidor use `0.0.0.0` y `PORT` de entorno.
- `No module named 'flask'`: añade a `requirements.txt` y redeploy.
- Índice Pinecone no existe: ejecuta `src/context_upload.py` para poblar.
- Tiempo de respuesta alto: reduce `k` del retriever o tamaño de fragmentos.
