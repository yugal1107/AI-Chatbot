from sqlalchemy.orm import Session
from ..models import document as document_model
from ..schemas import document_schema

def create_document_entry(db: Session, doc_data: document_schema.DocumentCreate):
    db_document = document_model.Document(
        original_filename=doc_data.original_filename,
        stored_filename=doc_data.stored_filename,
        pdf_file_path=doc_data.pdf_file_path,
        text_content_path=doc_data.text_content_path
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_document_by_id(db: Session, document_id: int):
    return db.query(document_model.Document).filter(document_model.Document.id == document_id).first()

def get_all_documents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(document_model.Document).offset(skip).limit(limit).all()
