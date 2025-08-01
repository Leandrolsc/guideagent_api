import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List

# LangChain imports for document processing and RAG
from langchain_community.vectorstores import Chroma
# A importação foi corrigida de Ollama para ChatOllama
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# --- Configuration ---
# Load configuration from environment variables
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
CHROMA_PERSIST_DIR = "./chroma_db"
TEMP_UPLOAD_DIR = "./temp_uploads"

# --- FastAPI App Initialization ---
app = FastAPI(
    title="RAG Platform API",
    description="API for vectorizing documents and chatting with them using RAG.",
    version="1.0.0"
)

# --- Data Models for API ---
class QueryRequest(BaseModel):
    text: str

class QueryResponse(BaseModel):
    response: str

# --- Core RAG Components Initialization ---
# Initialize embeddings and the LLM, connecting to the Ollama service
try:
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_HOST)
    # A classe foi corrigida de Ollama para ChatOllama
    llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_HOST)
except Exception as e:
    print(f"Error initializing Ollama components: {e}")
    # You might want to handle this more gracefully, but for now, we print and continue
    embeddings = None
    llm = None

# Initialize the Chroma vector store with persistence
vectorstore = Chroma(
    persist_directory=CHROMA_PERSIST_DIR,
    embedding_function=embeddings
)

# Create temporary directory for file uploads
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# --- Helper Functions ---
def process_document(file_path: str, file_type: str):
    """Loads and processes a document, splits it, and adds it to the vector store."""
    if file_type == 'pdf':
        loader = PyPDFLoader(file_path)
    elif file_type == 'docx':
        loader = UnstructuredWordDocumentLoader(file_path)
    elif file_type == 'md':
        loader = UnstructuredMarkdownLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    documents = loader.load()
    
    # Split documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    
    # Add chunks to the vector store
    vectorstore.add_documents(docs)
    print(f"Successfully processed and vectorized {len(docs)} chunks from {file_path}.")

def process_text(text: str):
    """Processes a raw text string, splits it, and adds it to the vector store."""
    doc = Document(page_content=text)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents([doc])
    vectorstore.add_documents(docs)
    print(f"Successfully processed and vectorized {len(docs)} chunks from raw text.")


# --- API Endpoints ---
@app.post("/upload", summary="Upload and process a file")
async def upload_file(file: UploadFile = File(...)):
    """
    Accepts a file (PDF, DOCX, MD), saves it temporarily, processes it,
    and vectorizes its content for storage.
    """
    if not any(file.filename.endswith(ext) for ext in ['.pdf', '.docx', '.md']):
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF, DOCX, or MD file.")

    file_path = os.path.join(TEMP_UPLOAD_DIR, file.filename)
    
    try:
        # Save the uploaded file to a temporary location
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_extension = file.filename.split('.')[-1].lower()
        process_document(file_path, file_extension)
        
        return {"status": "success", "filename": file.filename, "message": "File processed and vectorized successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/add_text", summary="Add and process raw text")
async def add_text(query: QueryRequest):
    """
    Accepts a raw text string, processes it, and vectorizes its content for storage.
    """
    try:
        process_text(query.text)
        return {"status": "success", "message": "Text processed and vectorized successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.post("/chat", summary="Chat with the documents", response_model=QueryResponse)
async def chat_with_docs(query: QueryRequest):
    """
    Receives a user query, retrieves relevant context from the vector store,
    and generates a response using the LLM.
    """
    if not llm:
        raise HTTPException(status_code=503, detail="LLM service is not available.")

    # Define the prompt template for the RAG chain
    prompt = ChatPromptTemplate.from_template("""
    Answer the following question based only on the provided context.
    If you don't know the answer, just say that you don't know. Don't try to make up an answer.

    <context>
    {context}
    </context>

    Question: {input}
    """)
    
    # Create the RAG chain
    document_chain = create_stuff_documents_chain(llm, prompt)
    
    # Get the retriever from the vector store
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3}) # Retrieve top 3 relevant chunks
    
    # Retrieve relevant documents
    retrieved_docs = retriever.invoke(query.text)
    
    # Invoke the chain with the retrieved context and the user's question
    response = document_chain.invoke({
        "input": query.text,
        "context": retrieved_docs
    })
    
    return QueryResponse(response=response)

@app.get("/", summary="Root endpoint")
def read_root():
    return {"message": "Welcome to the RAG API. Visit /docs for documentation."}
