from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import shutil
import os
import uuid # For generating unique filenames

from ..db.database import get_db
from ..crud import document_crud
from ..schemas import document_schema
from ..utils.pdf_parser import extract_text_from_pdf

from ..services import qa_service # We'll move some logic here or call new functions
from ..vector_store.chromadb_store import get_chroma_client, get_embedding_function, generate_collection_name
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma # LangChain's Chroma wrapper

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)

# Define base directories for storage
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Moves to backend/
UPLOADED_PDFS_DIR = os.path.join(BASE_DIR, "uploaded_pdfs")
EXTRACTED_TEXTS_DIR = os.path.join(BASE_DIR, "extracted_texts")

# Ensure these directories exist
os.makedirs(UPLOADED_PDFS_DIR, exist_ok=True)
os.makedirs(EXTRACTED_TEXTS_DIR, exist_ok=True)

@router.post("/upload", response_model=document_schema.DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf_and_extract_text(
    background_tasks: BackgroundTasks,  # FastAPI provided, no '=' from your side
    file: UploadFile = File(...),       # FastAPI default mechanism
    db: Session = Depends(get_db)       # FastAPI default mechanism (dependency)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are allowed."
        )

    original_filename = file.filename
    # Create a unique filename to prevent overwrites and handle special characters
    unique_id = uuid.uuid4().hex
    stored_pdf_filename = f"{unique_id}_{original_filename}"
    pdf_file_path = os.path.join(UPLOADED_PDFS_DIR, stored_pdf_filename)
    
    # Corresponding text file name
    text_filename = f"{unique_id}_{original_filename.rsplit('.', 1)[0]}.txt"
    text_file_path = os.path.join(EXTRACTED_TEXTS_DIR, text_filename)

    pdf_temp_file_path = None # For cleanup in case of error during text extraction

    try:
        # 1. Save the uploaded PDF file
        with open(pdf_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        pdf_temp_file_path = pdf_file_path # Mark for potential cleanup

        # 2. Extract text from the saved PDF
        extracted_text = extract_text_from_pdf(pdf_file_path)

        # 3. Save extracted text to a .txt file
        with open(text_file_path, "w", encoding="utf-8") as f_text:
            f_text.write(extracted_text)

        # 4. Create database entry
        doc_create_data = document_schema.DocumentCreate(
            original_filename=original_filename,
            stored_filename=stored_pdf_filename,
            pdf_file_path=pdf_file_path,
            text_content_path=text_file_path
        )
        db_document = document_crud.create_document_entry(db=db, doc_data=doc_create_data)

        # --- Background Task for ChromaDB Indexing ---
        collection_name = qa_service.generate_collection_name(db_document.id)
        chroma_client_instance = get_chroma_client() # Get the shared client
        embedding_func_instance = get_embedding_function() # Get the shared embedding function

        background_tasks.add_task(
            qa_service.index_document_to_chroma,
            db_document.id,
            extracted_text,
            collection_name,
            chroma_client_instance,
            embedding_func_instance
        )
        print(f"Background task added for indexing document ID: {db_document.id}")

        return db_document

    except Exception as e:
        # Clean up created files if any step fails
        if pdf_temp_file_path and os.path.exists(pdf_temp_file_path):
            os.remove(pdf_temp_file_path)
        if os.path.exists(text_file_path): # text_file_path might not be set if error is before
            os.remove(text_file_path)
        
        print(f"Error during PDF upload and processing: {e}") # Log the error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not process file: {str(e)}"
        )
    finally:
        await file.close()

@router.get("/{document_id}", response_model=document_schema.DocumentResponse)
def get_document_details(document_id: int, db: Session = Depends(get_db)):
    db_document = document_crud.get_document_by_id(db, document_id=document_id)
    if db_document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return db_document

@router.get("/", response_model=list[document_schema.DocumentResponse])
def list_all_documents(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    documents = document_crud.get_all_documents(db, skip=skip, limit=limit)
    return documents


@router.post("/{document_id}/ask", response_model=document_schema.AnswerResponse)
async def ask_question_on_document(
    document_id: int,
    request_body: document_schema.QuestionRequest, # This now includes chat_history
    db: Session = Depends(get_db)
):
    db_document = document_crud.get_document_by_id(db, document_id=document_id)
    if not db_document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    question = request_body.question
    chat_history_messages = request_body.chat_history # Extract chat_history

    try:
        answer = qa_service.get_answer_from_document_chroma(
            document_id,
            question,
            chat_history_messages # Pass it here
        )
        return document_schema.AnswerResponse(answer=answer)
    except qa_service.CollectionNotFoundError:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vector store collection for document ID {document_id} not found. It might still be indexing or indexing failed."
        )
    except Exception as e:
        print(f"Unhandled error in Q&A service call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while trying to answer the question: {str(e)}"
        )

    # if not db_document.text_content_path or not os.path.exists(db_document.text_content_path):
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Extracted text content for this document not found."
    #     )

    # # 2. Load the extracted text content
    # try:
    #     with open(db_document.text_content_path, "r", encoding="utf-8") as f:
    #         document_text = f.read()
    # except Exception as e:
    #     print(f"Error reading text file {db_document.text_content_path}: {e}")
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Could not read document content."
    #     )

    # if not document_text.strip():
    #     # If the file exists but is empty or only whitespace
    #     return document_schema.AnswerResponse(answer="The document content appears to be empty.")


    # # 3. Get answer using the Q&A service
    # question = request_body.question
    # try:
    #     answer = qa_service.get_answer_from_document(document_text, question)
    #     return document_schema.AnswerResponse(answer=answer)
    # except Exception as e:
    #     # This is a general catch-all. qa_service might handle some errors internally.
    #     print(f"Unhandled error in Q&A service call: {e}")
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"An error occurred while trying to answer the question: {str(e)}"
    #     )