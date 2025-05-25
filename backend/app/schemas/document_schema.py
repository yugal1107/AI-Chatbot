from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from typing import Optional, List, Dict, Any # Added List, Dict, Any

class DocumentBase(BaseModel):
    original_filename: str

class DocumentCreate(DocumentBase):
    stored_filename: str
    pdf_file_path: str
    text_content_path: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: int
    stored_filename: str
    upload_date: datetime
    pdf_file_path: str
    text_content_path: Optional[str] = None

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str

class ChatMessage(BaseModel):
    """Represents a single message in the chat history."""
    role: str # "user" or "assistant" (or "human"/"ai" if LangChain prefers)
    content: str

class QuestionRequest(BaseModel):
    question: str
    # chat_history is a list of previous Q&A pairs from the frontend
    # LangChain's memory often expects a list of BaseMessage objects,
    # but receiving a simpler structure and converting it is fine.
    # Let's expect a list of {'role': '...', 'content': '...'}
    chat_history: Optional[List[ChatMessage]] = Field(default_factory=list)

class AnswerResponse(BaseModel):
    answer: str
    # We could also return source documents if needed for the frontend
    # source_documents: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True # Replaces orm_mode in Pydantic v2
