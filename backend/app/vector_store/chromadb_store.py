import chromadb
import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings 

load_dotenv()

# Define base directory for ChromaDB persistence
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Moves to backend/
CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "chroma_db_data")
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    print(f"ChromaDB client initialized. Data will be persisted in: {CHROMA_PERSIST_DIR}")
except Exception as e:
    print(f"Error initializing ChromaDB client: {e}")
    chroma_client = chromadb.Client() 
    print("Warning: ChromaDB persistent client failed. Using in-memory client.")


# --- Embedding Function ---
# Ensure GOOGLE_API_KEY is set in your environment
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    
    print("CRITICAL: GOOGLE_API_KEY not found. Google Embeddings will fail.")


embedding_function_langchain = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-exp-03-07",
    google_api_key=GEMINI_API_KEY,
    task_type="retrieval_document" # Important for document embeddings
)


def get_chroma_client():
    """Returns the shared ChromaDB client instance."""
    return chroma_client

def get_embedding_function():
    """Returns the shared LangChain embedding function instance."""
    return embedding_function_langchain

def generate_collection_name(document_id: int) -> str:
    """Generates a consistent collection name for a document."""
    return f"doc_collection_{document_id}"
