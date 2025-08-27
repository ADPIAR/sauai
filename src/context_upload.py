#!/usr/bin/env python3
"""
Context Upload - Carga y procesamiento de documentos para RAG
Este módulo maneja la carga, splitting, embedding y almacenamiento de documentos en Pinecone
"""

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os
from pinecone import Pinecone, ServerlessSpec

class DocumentProcessor:
    """Clase para procesar y subir documentos a Pinecone"""
    
    def __init__(self, index_name="sauai"):
        """
        Inicializa el procesador de documentos
        
        Args:
            index_name (str): Nombre del índice en Pinecone
        """
        load_dotenv()
        self.index_name = index_name
        
        # Inicializar embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large"
        )
        
        # Inicializar Pinecone
        self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        
        # Configurar text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,  # Reducir de 500 a 300
            chunk_overlap=30,  # Reducir de 50 a 30
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_document(self, file_path):
        """
        Carga un documento de texto o PDF
        
        Args:
            file_path (str): Ruta al archivo
            
        Returns:
            list: Lista de documentos cargados
        """
        try:
            if file_path.endswith('.pdf'):
                from langchain_community.document_loaders import PyPDFLoader
                loader = PyPDFLoader(file_path)
            else:
                from langchain_community.document_loaders import TextLoader
                loader = TextLoader(file_path)
            
            documents = loader.load()
            print(f"✅ Documento cargado: {file_path}")
            return documents
        except Exception as e:
            print(f"❌ Error al cargar {file_path}: {e}")
            return []
    
    def split_documents(self, documents):
        """
        Divide los documentos en fragmentos más pequeños
        
        Args:
            documents (list): Lista de documentos a dividir
            
        Returns:
            list: Lista de fragmentos de documentos
        """
        if not documents:
            return []
            
        docs = self.text_splitter.split_documents(documents)
        print(f"✅ Documentos divididos en {len(docs)} fragmentos")
        return docs
    
    def create_or_get_index(self):
        """
        Crea o obtiene el índice de Pinecone
        
        Returns:
            pinecone.Index: Índice de Pinecone
        """
        try:
            if self.index_name not in self.pc.list_indexes().names():
                print(f"🔄 Creando índice '{self.index_name}' en Pinecone...")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=3072,  # Dimensión para text-embedding-3-large
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )            
                )
                print(f"✅ Índice '{self.index_name}' creado exitosamente")
            else:
                print(f"✅ Índice '{self.index_name}' ya existe")
            
            return self.pc.Index(self.index_name)
        except Exception as e:
            print(f"❌ Error al crear/obtener índice: {e}")
            raise
    
    def upload_documents_to_pinecone(self, docs):
        """
        Sube los documentos procesados a Pinecone en lotes
        
        Args:
            docs (list): Lista de fragmentos de documentos
            
        Returns:
            PineconeVectorStore: Almacén de vectores de Pinecone
        """
        try:
            # Crear o obtener índice
            index = self.create_or_get_index()
            
            # Procesar en lotes para evitar límites de tamaño
            BATCH_SIZE = 100  # Procesar de 100 en 100
            total_docs = len(docs)
            
            print(f"🔄 Subiendo {total_docs} fragmentos en lotes de {BATCH_SIZE}...")
            
            # Conectar al vector store existente
            docsearch = PineconeVectorStore(
                index_name=self.index_name,
                embedding=self.embeddings
            )
            
            # Procesar en lotes
            for i in range(0, total_docs, BATCH_SIZE):
                batch = docs[i:i+BATCH_SIZE]
                batch_num = (i // BATCH_SIZE) + 1
                total_batches = (total_docs + BATCH_SIZE - 1) // BATCH_SIZE
                
                print(f"📦 Procesando lote {batch_num}/{total_batches} ({len(batch)} documentos)...")
                
                # Agregar documentos al índice existente
                docsearch.add_documents(batch)
                
                print(f"✅ Lote {batch_num} completado")
            
            print(f"✅ Todos los documentos subidos exitosamente")
            return docsearch
            
        except Exception as e:
            print(f"❌ Error al subir documentos a Pinecone: {e}")
            raise
    
    def process_single_file(self, file_path):
        """
        Procesa un solo archivo: carga, divide y sube a Pinecone
        
        Args:
            file_path (str): Ruta al archivo a procesar
            
        Returns:
            PineconeVectorStore: Almacén de vectores de Pinecone
        """
        print(f"🔄 Procesando archivo: {file_path}")
        
        # Cargar documento
        documents = self.load_document(file_path)
        if not documents:
            raise ValueError(f"No se pudo cargar el documento: {file_path}")
        
        # Dividir en fragmentos
        docs = self.split_documents(documents)
        if not docs:
            raise ValueError(f"No se pudieron generar fragmentos del documento: {file_path}")
        
        # Subir a Pinecone
        docsearch = self.upload_documents_to_pinecone(docs)
        
        print(f"✅ Procesamiento completo de: {file_path}")
        return docsearch
    
    def process_multiple_files(self, file_paths):
        """
        Procesa múltiples archivos y los combina en un solo índice
        
        Args:
            file_paths (list): Lista de rutas a archivos
            
        Returns:
            PineconeVectorStore: Almacén de vectores de Pinecone
        """
        print(f"🔄 Procesando {len(file_paths)} archivos...")
        
        all_docs = []
        
        # Procesar cada archivo
        for file_path in file_paths:
            documents = self.load_document(file_path)
            if documents:
                docs = self.split_documents(documents)
                all_docs.extend(docs)
        
        if not all_docs:
            raise ValueError("No se pudieron procesar los documentos")
        
        print(f"🔄 Total de fragmentos a subir: {len(all_docs)}")
        
        # Subir todos los fragmentos
        docsearch = self.upload_documents_to_pinecone(all_docs)
        
        print(f"✅ Procesamiento completo de {len(file_paths)} archivos")
        return docsearch


# Función para seleccionar archivos interactivamente
def select_files_interactively():
    """Permite seleccionar archivos de la carpeta materials interactivamente"""
    import glob
    
    # Buscar archivos de texto en materials
    all_files = glob.glob('./materials/*.txt') + glob.glob('./materials/*.pdf')
    
    if not all_files:
        print("❌ No se encontraron archivos .txt o .pdf en ./materials/")
        return []
    
    print("\n📁 Archivos disponibles en ./materials/:")
    print("=" * 50)
    
    for i, file in enumerate(all_files, 1):
        filename = os.path.basename(file)
        print(f"{i}. {filename}")
    
    print("\n💡 Opciones:")
    print("• Escribe los números separados por comas (ej: 1,2,3)")
    print("• Escribe 'all' para seleccionar todos")
    print("• Presiona Enter para el archivo por defecto")
    
    selection = input("\n🔢 Tu selección: ").strip()
    
    if not selection:
        # Archivo por defecto
        default_file = './materials/el_plato_para_comer_saludable.txt'
        if os.path.exists(default_file):
            return [default_file]
        else:
            return [all_files[0]]
    
    if selection.lower() == 'all':
        return all_files
    
    try:
        # Procesar selección de números
        selected_nums = [int(x.strip()) for x in selection.split(',')]
        selected_files = []
        
        for num in selected_nums:
            if 1 <= num <= len(all_files):
                selected_files.append(all_files[num-1])
            else:
                print(f"⚠️ Número {num} fuera de rango, ignorado")
        
        return selected_files
    
    except ValueError:
        print("❌ Selección inválida, usando archivo por defecto")
        default_file = './materials/el_plato_para_comer_saludable.txt'
        return [default_file] if os.path.exists(default_file) else [all_files[0]]

# Ejecutar procesamiento
if __name__ == "__main__":
    import sys
    
    print("🚀 PROCESADOR DE DOCUMENTOS PARA RAG")
    print("=" * 50)
    
    # Inicializar procesador
    try:
        processor = DocumentProcessor()
        print("✅ Procesador inicializado correctamente")
    except Exception as e:
        print(f"❌ Error al inicializar procesador: {e}")
        sys.exit(1)
    
    # Seleccionar archivos
    if len(sys.argv) > 1:
        # Usar argumentos de línea de comandos
        selected_files = sys.argv[1:]
        print(f"📁 Archivos desde argumentos: {selected_files}")
    else:
        # Selección interactiva
        selected_files = select_files_interactively()
    
    if not selected_files:
        print("❌ No se seleccionaron archivos")
        sys.exit(1)
    
    print(f"\n🔄 Procesando {len(selected_files)} archivo(s)...")
    
    # Procesar archivos
    try:
        if len(selected_files) == 1:
            # Procesar archivo único
            docsearch = processor.process_single_file(selected_files[0])
        else:
            # Procesar múltiples archivos
            docsearch = processor.process_multiple_files(selected_files)
        
        print(f"\n✅ ¡Procesamiento completado exitosamente!")
        print(f"📊 Archivos procesados: {len(selected_files)}")
        print(f"🔗 Índice de Pinecone: {processor.index_name}")
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}") 