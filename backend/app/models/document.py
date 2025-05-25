from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..db.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, index=True)
    stored_filename = Column(String, unique=True) # e.g., UUID_original.pdf
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    pdf_file_path = Column(String)
    text_content_path = Column(String, nullable=True) # Path to the extracted .txt file
