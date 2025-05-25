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
    # Add other origins if your frontend runs elsewhere
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

# Optional: A simple endpoint to test Gemini LLM integration (can be removed later)
# from langchain_google_genai import ChatGoogleGenerativeAI
# import os
# @app.get("/test-gemini", tags=["LLM Test"])
# async def test_gemini():
#     try:
#         api_key = os.getenv("GOOGLE_API_KEY")
#         if not api_key:
#             return {"error": "GOOGLE_API_KEY not found"}
#         llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key, convert_system_message_to_human=True)
#         response = await llm.ainvoke("Tell me a short joke about AI.")
#         return {"joke": response.content}
#     except Exception as e:
#         return {"error": str(e)}
