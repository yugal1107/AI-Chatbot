import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS # For in-memory vector store
# from langchain.document_loaders import TextLoader # If loading from .txt file
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage # For populating memory

from langchain_community.vectorstores import Chroma # LangChain's Chroma wrapper
from ..vector_store.chromadb_store import get_chroma_client, get_embedding_function, generate_collection_name
from typing import List, Dict, Any # For type hinting chat_history
from ..schemas.document_schema import ChatMessage



load_dotenv()

# Initialize LLM and Embeddings
# Ensure GOOGLE_API_KEY is set in your environment
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, convert_system_message_to_human=True)
# Using Google's embedding model is often a good pair with their LLMs
# If you prefer a local/free embedding model:
# from langchain_community.embeddings import HuggingFaceEmbeddings
# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=GEMINI_API_KEY)

class CollectionNotFoundError(Exception):
    """Custom exception for when a ChromaDB collection is not found."""
    pass

def get_answer_from_document_chroma(
    document_id: int,
    question: str,
    chat_history_messages: List[ChatMessage] # Expecting our Pydantic model
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

        # Initialize memory with the provided chat history
        # LangChain memory expects specific message types (HumanMessage, AIMessage)
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True, # Important for ConversationalRetrievalChain
            output_key='answer' # Ensure the output key matches what the chain produces
        )

        # Populate memory from the input chat_history_messages
        for msg in chat_history_messages:
            if msg.role.lower() == "user" or msg.role.lower() == "human":
                memory.chat_memory.add_message(HumanMessage(content=msg.content))
            elif msg.role.lower() == "assistant" or msg.role.lower() == "ai":
                memory.chat_memory.add_message(AIMessage(content=msg.content))
        
        # You might want a more sophisticated condense_question_prompt
        # if the history gets very long, but default often works okay.
        # Example custom prompt for the question generation step (optional)
        # _template = """Given the following conversation and a follow up question, rephrase the
        # follow up question to be a standalone question, in its original language.
        # If the follow up question is already a standalone question, just return it as is.

        # Chat History:
        # {chat_history}
        # Follow Up Input: {question}
        # Standalone question:"""
        # CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)


        # Create the ConversationalRetrievalChain
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=False, # Set to True if you want to inspect sources
            # condense_question_prompt=CONDENSE_QUESTION_PROMPT, # Optional
            verbose=True # Good for debugging
        )

        print(f"Asking LLM (Conversational w/ Chroma for doc {document_id}): {question}")
        # The input to this chain is typically just the 'question'
        result = qa_chain.invoke({"question": question})
        print(f"LLM Result: {result}")

        # The answer is usually in result['answer'] for ConversationalRetrievalChain
        return result.get("answer", "No answer found from the document context.")

    except CollectionNotFoundError:
        raise
    except Exception as e:
        print(f"Error during Q&A processing with ChromaDB for document {document_id}: {e}")
        # Log the full traceback for better debugging
        import traceback
        traceback.print_exc()
        return f"An error occurred while processing your question with ChromaDB: {str(e)}"
    

# def get_answer_from_document_chroma(document_id: int, question: str) -> str:
#     collection_name = generate_collection_name(document_id)
#     chroma_client_instance = get_chroma_client()
#     embedding_func_instance = get_embedding_function()

#     try:
#         # Check if collection exists using the raw client first
#         # This is more direct than trying to instantiate LangChain's Chroma and catching its error
#         try:
#             chroma_client_instance.get_collection(name=collection_name)
#             print(f"Found existing ChromaDB collection: {collection_name}")
#         except Exception as e: # More specific exception from chromadb library is better
#             print(f"ChromaDB collection '{collection_name}' not found for document_id {document_id}. Error: {e}")
#             raise CollectionNotFoundError(f"Collection '{collection_name}' not found.")


#         # Instantiate LangChain's Chroma vector store for querying
#         vector_store = Chroma(
#             collection_name=collection_name,
#             embedding_function=embedding_func_instance,
#             client=chroma_client_instance, # Pass the initialized client
#             # persist_directory=CHROMA_PERSIST_DIR # Not needed if client is persistent
#         )
#         print(f"Successfully connected to ChromaDB collection: {collection_name} for querying.")

#         retriever = vector_store.as_retriever(search_kwargs={"k": 3})

#         prompt_template = """Use the following pieces of context to answer the question at the end.
#         If you don't know the answer from the context, just say that you don't know, don't try to make up an answer.
#         Keep the answer concise and relevant to the context provided.

#         Context:
#         {context}

#         Question: {question}

#         Helpful Answer:"""
#         QA_PROMPT = PromptTemplate(
#             template=prompt_template, input_variables=["context", "question"]
#         )

#         qa_chain = RetrievalQA.from_chain_type(
#             llm=llm,
#             chain_type="stuff",
#             retriever=retriever,
#             return_source_documents=False,
#             chain_type_kwargs={"prompt": QA_PROMPT}
#         )

#         print(f"Asking LLM (via ChromaDB retrieved context for doc {document_id}): {question}")
#         result = qa_chain.invoke({"query": question})
#         print(f"LLM Result: {result}")

#         return result.get("result", "No answer found from the document context.")

#     except CollectionNotFoundError: # Re-raise our custom exception
#         raise
#     except Exception as e:
#         print(f"Error during Q&A processing with ChromaDB for document {document_id}: {e}")
#         return f"An error occurred while processing your question with ChromaDB: {str(e)}"

# def get_answer_from_document(document_text: str, question: str) -> str:
#     if not document_text:
#         return "The document content is empty or could not be loaded."

#     # 1. Split the document text into chunks
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1000, # Adjust as needed
#         chunk_overlap=150  # Adjust as needed
#     )
#     # LangChain's FAISS.from_texts can take raw text strings directly
#     texts = text_splitter.split_text(document_text)

#     if not texts:
#         return "Could not split the document into processable chunks."

#     try:
#         # 2. Create an in-memory vector store from the chunks
#         # This creates embeddings and the index on the fly
#         print(f"Creating in-memory vector store with {len(texts)} chunks...")
#         vector_store = FAISS.from_texts(texts, embeddings)
#         print("In-memory vector store created.")

#         # 3. Create a retriever
#         retriever = vector_store.as_retriever(search_kwargs={"k": 3}) # Get top 3 relevant chunks

#         # 4. Optional: Define a custom prompt template
#         prompt_template = """Use the following pieces of context to answer the question at the end.
#         If you don't know the answer, just say that you don't know, don't try to make up an answer.
#         Keep the answer concise and relevant to the context provided.

#         Context:
#         {context}

#         Question: {question}

#         Helpful Answer:"""
#         QA_PROMPT = PromptTemplate(
#             template=prompt_template, input_variables=["context", "question"]
#         )

#         # 5. Create the RetrievalQA chain
#         qa_chain = RetrievalQA.from_chain_type(
#             llm=llm,
#             chain_type="stuff", # "stuff" passes all retrieved chunks in one go
#                               # consider "map_reduce" or "refine" for very large contexts
#                               # that might exceed Gemini's token limit even after retrieval.
#             retriever=retriever,
#             return_source_documents=True, # Set to True if you want to see which chunks were used
#             chain_type_kwargs={"prompt": QA_PROMPT}
#         )

#         # 6. Get the answer
#         print(f"Asking LLM: {question}")
#         result = qa_chain.invoke({"query": question}) # Use invoke for newer LangChain
#         print(f"LLM Result: {result}")

#         return result.get("result", "No answer found.")

#     except Exception as e:
#         print(f"Error during Q&A processing: {e}")
#         # Consider more specific error handling or logging
#         return f"An error occurred while processing your question: {str(e)}"

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