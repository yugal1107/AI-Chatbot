# backend/app/services/qa_service.py
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Sequence, TypedDict, Annotated

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END, add_messages

from ..vector_store.chromadb_store import get_chroma_client, get_embedding_function, generate_collection_name
from ..schemas.document_schema import ChatMessage

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY, convert_system_message_to_human=True)
langgraph_memory_checkpointer = MemorySaver()

class RAGLangGraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    document_id: int
    current_question: str
    retrieved_context: List[str]

class CollectionNotFoundError(Exception):
    pass

def retrieve_context_node(state: RAGLangGraphState):
    document_id = state["document_id"]
    if not state["messages"] or not isinstance(state["messages"][-1], HumanMessage):
        return {"retrieved_context": []}

    question_for_retrieval = state["messages"][-1].content
    collection_name = generate_collection_name(document_id)
    chroma_client_instance = get_chroma_client()
    embedding_func_instance = get_embedding_function()

    try:
        chroma_client_instance.get_collection(name=collection_name)
    except Exception as e:
        raise CollectionNotFoundError(f"Collection '{collection_name}' not found.") from e

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_func_instance,
        client=chroma_client_instance,
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    retrieved_docs = retriever.invoke(question_for_retrieval)
    context_str_list = [doc.page_content for doc in retrieved_docs]
    return {"retrieved_context": context_str_list}

def generate_answer_node(state: RAGLangGraphState):
    context = "\n\n".join(state["retrieved_context"])
    conversation_messages = list(state["messages"])

    rag_prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a helpful assistant. Use the following pieces of context to answer the user's question. "
            "Keep your answer concise.\n\n"
            "Context:\n{context}"
        )),
        MessagesPlaceholder(variable_name="messages")
    ])

    rag_chain = rag_prompt_template | llm | StrOutputParser()
    ai_response_content = rag_chain.invoke({
        "context": context,
        "messages": conversation_messages
    })

    return {"messages": [AIMessage(content=ai_response_content)]}

rag_workflow_builder = StateGraph(RAGLangGraphState)
rag_workflow_builder.add_node("retrieve_context", retrieve_context_node)
rag_workflow_builder.add_node("generate_answer", generate_answer_node)
rag_workflow_builder.add_edge(START, "retrieve_context")
rag_workflow_builder.add_edge("retrieve_context", "generate_answer")
langgraph_app = rag_workflow_builder.compile(checkpointer=langgraph_memory_checkpointer)

def get_answer_from_document_chroma(
    document_id: int,
    question: str,
    chat_history_messages: List[ChatMessage]
) -> str:
    langchain_history = []
    for msg in chat_history_messages:
        if msg.role.lower() in ["user", "human"]:
            langchain_history.append(HumanMessage(content=msg.content))
        elif msg.role.lower() in ["assistant", "ai"]:
            langchain_history.append(AIMessage(content=msg.content))
    
    current_question_lm = HumanMessage(content=question)
    all_messages_for_graph_turn = langchain_history + [current_question_lm]

    initial_graph_state = {
        "messages": all_messages_for_graph_turn,
        "document_id": document_id,
    }

    thread_id = f"doc_thread_{document_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        final_state = langgraph_app.invoke(initial_graph_state, config=config)

        if final_state and final_state.get("messages"):
            ai_answer_message = final_state["messages"][-1]
            if isinstance(ai_answer_message, AIMessage):
                return ai_answer_message.content
            else:
                return "Error: Could not determine AI response."
        else:
            return "Error: Failed to process the request with LangGraph."

    except CollectionNotFoundError as e:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"An error occurred while processing your question: {str(e)}"

def index_document_to_chroma(
    document_id: int,
    document_text: str,
    collection_name: str,
    chroma_client_instance,
    embedding_func_instance
):
    if not document_text:
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_text(document_text)

    if not chunks:
        return

    try:
        try:
            chroma_client_instance.get_collection(name=collection_name)
            chroma_client_instance.delete_collection(name=collection_name)
        except:
            pass

        vector_store = Chroma.from_texts(
            texts=chunks,
            embedding=embedding_func_instance,
            collection_name=collection_name,
            client=chroma_client_instance,
        )
    except Exception as e:
        raise