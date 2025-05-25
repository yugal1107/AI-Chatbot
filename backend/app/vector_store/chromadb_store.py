import chromadb
import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings # Or your chosen embedding function

load_dotenv()

# Define base directory for ChromaDB persistence
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Moves to backend/
CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "chroma_db_data")
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# Initialize ChromaDB client (persistent)
# This client can be shared across different parts of the application
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    print(f"ChromaDB client initialized. Data will be persisted in: {CHROMA_PERSIST_DIR}")
except Exception as e:
    print(f"Error initializing ChromaDB client: {e}")
    # Fallback to in-memory if persistent fails, or raise an error
    # For a production app, you'd want more robust error handling or configuration options
    chroma_client = chromadb.Client() # In-memory fallback
    print("Warning: ChromaDB persistent client failed. Using in-memory client.")


# --- Embedding Function ---
# Ensure GOOGLE_API_KEY is set in your environment
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    # This is a critical error for Google embeddings, handle appropriately
    print("CRITICAL: GOOGLE_API_KEY not found. Google Embeddings will fail.")
    # Depending on policy, either raise an error or allow app to start with a warning
    # if you have alternative non-API embedding logic.
    # For now, we'll let it proceed and it will fail if GoogleEmbeddings is used without a key.

# You can use Google's embedding model or a local one like Sentence Transformers
# This embedding function instance will be used by LangChain's Chroma vector store wrapper.
embedding_function_langchain = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-exp-03-07",
    google_api_key=GEMINI_API_KEY,
    task_type="retrieval_document" # Important for document embeddings
)
# Alternatively, for local embeddings:
# from langchain_community.embeddings import HuggingFaceEmbeddings
# embedding_function_langchain = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_chroma_client():
    """Returns the shared ChromaDB client instance."""
    return chroma_client

def get_embedding_function():
    """Returns the shared LangChain embedding function instance."""
    return embedding_function_langchain

def generate_collection_name(document_id: int) -> str:
    """Generates a consistent collection name for a document."""
    return f"doc_collection_{document_id}"

# Note: The actual creation of LangChain's Chroma vector store object
# will happen in the service layer where documents and questions are handled.
# This file primarily sets up the client and embedding function.