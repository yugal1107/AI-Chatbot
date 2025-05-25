from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .db.database import engine
from .models import document # This imports the models module
from .routers import upload_router
from .routers import qa_router


load_dotenv()

# Create database tables if they don't exist
# This should be called after all models are defined and imported
document.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PDF Q&A Backend",
    description="API for uploading PDFs and asking questions about their content.",
    version="0.1.0"
)

# CORS (Cross-Origin Resource Sharing)
# Adjust origins as needed for your frontend
origins = [
    "http://localhost:5173",  # Default React dev server
    "http://127.0.0.1:5173",
    "https://ai-chatbot-black-one.vercel.app/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the PDF Q&A API!"}

# Include routers
app.include_router(upload_router.router)