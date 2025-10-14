# RAG (OpenAI + Pinecone) - Detallado

RAG (Retrieval-Augmented Generation) combina búsqueda semántica con generación para respuestas con contexto.

## Pipeline
1. Embeddings: OpenAI convierte textos a vectores numéricos.
2. Vector store: Pinecone almacena y busca los vectores.
3. Retriever: dado un query, trae los fragmentos más relevantes.
4. LLM: OpenAI recibe fragmentos + pregunta y genera la respuesta.

## Componentes en el código
- `OpenAIEmbeddings` y `ChatOpenAI` (LangChain + OpenAI).
- `PineconeVectorStore` para conectarse al índice existente.
- `RetrievalQA` para unir retrieval y generación.

## Parámetros y tamaños
- `k` documentos recuperados (ej. 3). Ajusta para balancear precisión/latencia.
- Longitud de contexto: textos muy largos pueden subir costes/latencia.

## Preparación del índice
- Crear y poblar índice con `src/context_upload.py`.
- Verificar existencia del índice en `RAG_ChatBot` (falla si no existe).

## Troubleshooting
- "Índice no existe": crea el índice y sube los documentos.
- "Timeouts o latencia alta": reduce `k` o el tamaño de fragmentos.
- "Respuestas fuera de tema": mejora el contexto y el prompt del sistema.
- "Errores de API": revisa `OPENAI_API_KEY` y `PINECONE_API_KEY`.
