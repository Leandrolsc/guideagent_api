import os
import shutil
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:1b")
CHROMA_PERSIST_DIR = "./chroma_db"
TEMP_UPLOAD_DIR = "./temp_uploads"

app = FastAPI(
    title="RAG Platform API with Structured Metadata",
    description="API for vectorizing documents with structured metadata and chatting with them.",
    version="1.2.1"
)

class QueryRequest(BaseModel):
    text: str

class Source(BaseModel):
    title: str
    link: Optional[str] = None
    filename: str

class QueryResponse(BaseModel):
    response: str
    sources: List[Source] # Modelo de resposta aprimorado

# --- Core RAG Components Initialization ---
try:
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_HOST)
    llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_HOST)
except Exception as e:
    print(f"Error initializing Ollama components: {e}")
    embeddings = None
    llm = None

vectorstore = Chroma(
    persist_directory=CHROMA_PERSIST_DIR,
    embedding_function=embeddings
)

os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# --- Helper Functions ---
def process_document(file_path: str, file_type: str, custom_metadata: dict):
    """Loads a document, adds custom metadata, splits it, and adds to the vector store."""
    if file_type == 'pdf':
        loader = PyPDFLoader(file_path)
    elif file_type == 'docx':
        loader = UnstructuredWordDocumentLoader(file_path)
    elif file_type == 'md':
        loader = UnstructuredMarkdownLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    documents = loader.load()
    
    for doc in documents:
        doc.metadata.update(custom_metadata)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    
    vectorstore.add_documents(docs)
    print(f"Successfully processed and vectorized {len(docs)} chunks from {custom_metadata.get('filename')}.")

# --- API Endpoints ---
@app.post("/upload", summary="Upload and process a file with structured metadata")
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(..., description="Title of the document"),
    link: Optional[str] = Form(default=None, description="Link to the original document"),
    keywords: str = Form(default='[]', description='JSON string of a list of keywords')
):
    """
    Accepts a file and its structured metadata, processes it,
    and vectorizes its content for storage.
    """
    file_path = os.path.join(TEMP_UPLOAD_DIR, file.filename)
    
    try:
        try:
            keywords_list = json.loads(keywords)
            if not isinstance(keywords_list, list):
                raise ValueError("Keywords must be a JSON list of strings.")
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid keywords format: {e}")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_extension = file.filename.split('.')[-1].lower()
        
        custom_metadata = {
            "title": title,
            "link": link,
            "filename": file.filename,
            "keywords": "; ".join(keywords_list)
        }

        process_document(file_path, file_extension, custom_metadata)
        
        return {"status": "success", "filename": file.filename, "message": "File and metadata processed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/chat", summary="Chat with the documents", response_model=QueryResponse)
async def chat_with_docs(query: QueryRequest):
    """
    Receives a query, retrieves context, generates a response, and cites sources.
    """
    if not llm:
        raise HTTPException(status_code=503, detail="LLM service is not available.")

    # Prompt atualizado para informar ao LLM que o contexto contém metadados
    prompt = ChatPromptTemplate.from_template("""
    Answer the following question based only on the provided context.
    The context for each document chunk includes its title, link, and keywords. Use them if the question asks for it.
    If you don't know the answer, just say that you don't know.

    <context>
    {context}
    </context>

    Question: {input}
    """)
    
    document_chain = create_stuff_documents_chain(llm, prompt)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    retrieved_docs = retriever.invoke(query.text)
    
    # Cria uma nova lista de documentos onde os metadados são pré-anexados ao conteúdo.
    # Isso torna os metadados visíveis para o LLM dentro do contexto.
    context_with_metadata = []
    for doc in retrieved_docs:
        metadata = doc.metadata
        header = f"--- Source Document ---\n"
        header += f"Title: {metadata.get('title', 'N/A')}\n"
        if metadata.get('link'):
            header += f"Link: {metadata.get('link')}\n"
        if metadata.get('keywords'):
            header += f"Keywords: {metadata.get('keywords')}\n"
        header += f"-----------------------\n\n"
        
        # Cria um novo documento com o cabeçalho pré-anexado ao conteúdo original.
        context_doc = Document(
            page_content=header + doc.page_content,
            metadata=metadata # Mantém os metadados originais para a citação da fonte
        )
        context_with_metadata.append(context_doc)

    # Extrai os metadados de forma estruturada para a resposta da API, evitando duplicatas
    sources_dict = {}
    for doc in retrieved_docs:
        filename = doc.metadata.get("filename", "unknown")
        if filename not in sources_dict:
            sources_dict[filename] = {
                "title": doc.metadata.get("title", filename),
                "link": doc.metadata.get("link"),
                "filename": filename
            }
    sources = [Source(**data) for data in sources_dict.values()]
    
    # Invoca a cadeia com o contexto enriquecido
    response_text = document_chain.invoke({
        "input": query.text,
        "context": context_with_metadata # Usa a nova lista de documentos
    })
    
    return QueryResponse(response=response_text, sources=sources)

@app.get("/", summary="Root endpoint")
def read_root():
    return {"message": "Welcome to the RAG API with Structured Metadata. Visit /docs for documentation."}
