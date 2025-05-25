# backend/app/services/qa_service.py
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Sequence, TypedDict, Annotated

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder # For constructing prompts
from langchain_core.output_parsers import StrOutputParser


# LangGraph imports
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END, add_messages

# Local imports
from ..vector_store.chromadb_store import get_chroma_client, get_embedding_function, generate_collection_name
from ..schemas.document_schema import ChatMessage # Your Pydantic model

load_dotenv()

# --- Initialize LLM and Checkpointer (globally or cached for efficiency) ---
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, convert_system_message_to_human=True)

langgraph_memory_checkpointer = MemorySaver() # In-memory checkpointer


# --- Define LangGraph State ---
class RAGLangGraphState(TypedDict):
    # `messages` will store the conversation history.
    # `add_messages` is a special operator that appends new messages to the existing list.
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Information needed for the RAG process within a single turn
    document_id: int              # To know which document's ChromaDB collection to use
    current_question: str         # The latest question from the user for this turn
    retrieved_context: List[str]  # Context chunks retrieved from ChromaDB


# --- Define LangGraph Nodes ---

def retrieve_context_node(state: RAGLangGraphState):
    """Retrieves context from ChromaDB based on the current question and document_id."""
    print(f"LG_NODE: Retrieving context for doc_id: {state['document_id']}")
    document_id = state["document_id"]
    # The current question is the last message in the 'messages' list
    # Ensure messages list is not empty and last message is HumanMessage
    if not state["messages"] or not isinstance(state["messages"][-1], HumanMessage):
        # This case should be handled by how initial_graph_state is constructed
        print("LG_NODE_ERROR: No human question found in messages for retrieval.")
        return {"retrieved_context": []}

    question_for_retrieval = state["messages"][-1].content

    collection_name = generate_collection_name(document_id)
    chroma_client_instance = get_chroma_client()
    embedding_func_instance = get_embedding_function()

    try:
        # Ensure collection exists (basic check)
        chroma_client_instance.get_collection(name=collection_name)
    except Exception as e: # Replace with more specific ChromaDB exception if available
        print(f"LG_NODE_ERROR: ChromaDB collection '{collection_name}' not found. Error: {e}")
        # Optionally, raise a specific error or return empty context
        raise CollectionNotFoundError(f"Collection '{collection_name}' not found.") from e

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_func_instance,
        client=chroma_client_instance,
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 3}) # Get top 3 chunks
    retrieved_docs = retriever.invoke(question_for_retrieval)
    context_str_list = [doc.page_content for doc in retrieved_docs]
    print(f"LG_NODE: Retrieved {len(context_str_list)} context chunks.")
    return {"retrieved_context": context_str_list}


def generate_answer_node(state: RAGLangGraphState):
    """Generates an answer using the LLM, retrieved context, and conversation history."""
    print("LG_NODE: Generating answer")
    context = "\n\n".join(state["retrieved_context"])
    conversation_messages = list(state["messages"]) # Full history including current question

    # Define the prompt for the LLM
    # System message provides instructions and context
    # MessagesPlaceholder takes the history
    rag_prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a helpful assistant. Use the following pieces of context to answer the user's question. "
            "If you don't know the answer from the provided context, just say that you don't know. "
            "Don't try to make up an answer. Keep your answer concise.\n\n"
            "Context:\n{context}"
        )),
        MessagesPlaceholder(variable_name="messages")
    ])

    # Create the chain: prompt | llm | output_parser
    rag_chain = rag_prompt_template | llm | StrOutputParser()

    # Invoke the chain
    # The `messages` in the state already include the latest user question
    ai_response_content = rag_chain.invoke({
        "context": context,
        "messages": conversation_messages
    })

    print(f"LG_NODE: LLM generated answer: {ai_response_content}")
    # The graph expects a dictionary where keys match the state,
    # and `add_messages` will append this AIMessage.
    return {"messages": [AIMessage(content=ai_response_content)]}


# --- Build and Compile LangGraph Application (done once) ---
rag_workflow_builder = StateGraph(RAGLangGraphState)

rag_workflow_builder.add_node("retrieve_context", retrieve_context_node)
rag_workflow_builder.add_node("generate_answer", generate_answer_node)

# Define edges: START -> retrieve_context -> generate_answer -> END
rag_workflow_builder.add_edge(START, "retrieve_context")
rag_workflow_builder.add_edge("retrieve_context", "generate_answer")
# By not adding an edge from generate_answer to END, it implicitly ends.
# Or explicitly: rag_workflow_builder.add_edge("generate_answer", END)

langgraph_app = rag_workflow_builder.compile(checkpointer=langgraph_memory_checkpointer)
print("LangGraph RAG application compiled with MemorySaver.")


# --- Custom Exception ---
class CollectionNotFoundError(Exception):
    pass


# --- Updated Service Function ---
def get_answer_from_document_chroma(
    document_id: int,
    question: str,
    chat_history_messages: List[ChatMessage] # List of Pydantic ChatMessage objects
) -> str:
    print(f"LG_SERVICE: Received question for doc_id {document_id}: '{question}'")
    print(f"LG_SERVICE: Received chat history with {len(chat_history_messages)} messages.")

    # 1. Convert incoming Pydantic ChatMessages and new question to LangChain BaseMessages
    langchain_history = []
    for msg in chat_history_messages:
        if msg.role.lower() in ["user", "human"]:
            langchain_history.append(HumanMessage(content=msg.content))
        elif msg.role.lower() in ["assistant", "ai"]:
            langchain_history.append(AIMessage(content=msg.content))
    
    current_question_lm = HumanMessage(content=question)
    all_messages_for_graph_turn = langchain_history + [current_question_lm]

    # 2. Prepare initial state for this graph invocation
    # This state is passed to the graph. If a checkpoint exists for the thread_id,
    # LangGraph will load it and merge this input. `add_messages` appends.
    # Other keys might overwrite or be new.
    initial_graph_state = {
        "messages": all_messages_for_graph_turn,
        "document_id": document_id,
        # current_question is implicitly the last human message in "messages"
        # but can be passed if nodes need it explicitly before history is fully formed.
        # For this RAG structure, nodes will derive it from messages.
    }

    # 3. Define a configuration for the LangGraph invocation, including a thread_id.
    # The thread_id groups related interactions. For your stateless backend where history
    # is passed in, you might use a document-specific thread ID. If multiple users
    # chat with the same doc, their histories would mix if not further distinguished.
    # For simplicity, let's use a document-specific ID.
    # If your frontend could manage a session_id, that would be better for true multi-user.
    thread_id = f"doc_thread_{document_id}"
    config = {"configurable": {"thread_id": thread_id}}
    print(f"LG_SERVICE: Using thread_id: {thread_id}")

    try:
        # 4. Invoke the LangGraph application
        # The `langgraph_app` will manage the state persistence via `MemorySaver`
        # based on the `thread_id` in the config.
        print(f"LG_SERVICE: Invoking LangGraph app with {len(all_messages_for_graph_turn)} total messages for this turn.")
        final_state = langgraph_app.invoke(initial_graph_state, config=config)

        # 5. Extract the latest AI message as the answer
        if final_state and final_state.get("messages"):
            # The last message added by generate_answer_node should be the AI's response
            ai_answer_message = final_state["messages"][-1]
            if isinstance(ai_answer_message, AIMessage):
                print(f"LG_SERVICE: Successfully got AI answer: {ai_answer_message.content}")
                return ai_answer_message.content
            else:
                print("LG_SERVICE_ERROR: Last message in final state was not an AIMessage.")
                return "Error: Could not determine AI response."
        else:
            print("LG_SERVICE_ERROR: LangGraph invocation did not return expected final state or messages.")
            return "Error: Failed to process the request with LangGraph."

    except CollectionNotFoundError as e:
        print(f"LG_SERVICE_ERROR: Collection not found - {str(e)}")
        # This custom exception should be caught by the router to return 404
        raise # Re-raise for the router to handle
    except Exception as e:
        print(f"LG_SERVICE_ERROR: Unhandled error during LangGraph Q&A processing for document {document_id}: {e}")
        import traceback
        traceback.print_exc()
        return f"An error occurred while processing your question: {str(e)}"

# In your router, you'd now call get_answer_from_document_chroma_langgraph
# and ensure qa_service.CollectionNotFoundError is handled for a 404.

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