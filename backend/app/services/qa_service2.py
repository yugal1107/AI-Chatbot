import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ChatMessageHistory
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, AIMessage
from typing import List
from ..vector_store.chromadb_store import get_chroma_client, get_embedding_function, generate_collection_name
from ..schemas.document_schema import ChatMessage
import traceback

load_dotenv()

# Initialize LLM and Embeddings
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, convert_system_message_to_human=True)
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=GEMINI_API_KEY)

class CollectionNotFoundError(Exception):
    pass

def get_answer_from_document_chroma(
    document_id: int,
    question: str,
    chat_history_messages: List[ChatMessage]
) -> str:
    collection_name = generate_collection_name(document_id)
    chroma_client_instance = get_chroma_client()
    embedding_func_instance = get_embedding_function()

    try:
        try:
            chroma_client_instance.get_collection(name=collection_name)
            print(f"Found existing ChromaDB collection: {collection_name}")
        except Exception as e:
            print(f"ChromaDB collection '{collection_name}' not found for document_id {document_id}. Error: {e}")
            raise CollectionNotFoundError(f"Collection '{collection_name}' not found.")

        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_func_instance,
            client=chroma_client_instance,
        )
        print(f"Successfully connected to ChromaDB collection: {collection_name} for querying.")

        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        # Initialize ChatMessageHistory
        history = ChatMessageHistory()
        for msg in chat_history_messages:
            if msg.role.lower() in ["user", "human"]:
                history.add_user_message(msg.content)
            elif msg.role.lower() in ["assistant", "ai"]:
                history.add_ai_message(msg.content)

        # Define custom prompt with history and context
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an assistant answering questions based on a document. Use the provided context and chat history to give accurate, concise answers. If the answer isn't in the context, say so.\n\nContext: {context}\nHistory: {history}"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}")
        ])

        # Create LCEL chain
        chain = (
            {
                "context": retriever,
                "history": lambda x: history.messages,
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
        )

        print(f"Asking LLM (via ChromaDB retrieved context for doc {document_id}): {question}")
        result = chain.invoke(question)
        print(f"LLM Result: {result.content}")

        return result.content

    except CollectionNotFoundError:
        raise
    except Exception as e:
        print(f"Error during Q&A processing with ChromaDB for document {document_id}: {e}")
        traceback.print_exc()
        return f"An error occurred while processing your question with ChromaDB: {str(e)}"
    

def index_document_to_chroma(
    document_id: int,
    document_text: str,
    collection_name: str,
    chroma_client_instance, # Pass the client instance
    embedding_func_instance  # Pass the embedding function instance
):
    print(f"Starting indexing for document_id: {document_id} into collection: {collection_name}")
    if not document_text:
        print(f"No text to index for document_id: {document_id}")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_text(document_text)

    if not chunks:
        print(f"Text splitting resulted in no chunks for document_id: {document_id}")
        return

    # Using LangChain's Chroma wrapper to add texts
    # This will create the collection if it doesn't exist or add to it.
    # It handles the embedding generation internally using the provided embedding_function.
    try:
        # Check if collection exists, if so, maybe delete and recreate or handle updates
        try:
            chroma_client_instance.get_collection(name=collection_name)
            print(f"Collection {collection_name} already exists. Deleting and recreating for fresh indexing.")
            chroma_client_instance.delete_collection(name=collection_name)
        except: # chromadb.errors.CollectionNotFoundException or similar specific exception is better
            print(f"Collection {collection_name} does not exist. Creating new one.")
            pass # Collection does not exist, proceed to create


        # Create a LangChain Chroma vector store instance
        # This step implicitly creates the collection in ChromaDB if it doesn't exist
        # and adds the documents.
        vector_store = Chroma.from_texts(
            texts=chunks,
            embedding=embedding_func_instance,
            collection_name=collection_name,
            client=chroma_client_instance, # Pass the initialized client
            # persist_directory=CHROMA_PERSIST_DIR # Not needed if client is persistent
        )
        # vector_store.persist() # Call persist if client is not persistent or to be extra sure

        print(f"Successfully indexed {len(chunks)} chunks for document_id: {document_id} into ChromaDB collection: {collection_name}")
    except Exception as e:
        print(f"Error indexing document {document_id} to ChromaDB: {e}")
        # Consider how to handle partial failures or rollback
        raise # Re-raise to be caught by the endpoint