# PDF Q&A Chatbot with LangChain, Gemini, FastAPI, React, and ChromaDB

This project is a full-stack application that allows users to upload PDF documents and ask questions regarding their content. The backend processes these documents using natural language processing (NLP) with LangChain and Google's Gemini model, and a React frontend provides an interactive chat interface.

**Live Demo (if applicable):** [Link to your live demo]

**Features:**

*   **PDF Upload:** Users can upload PDF documents.
*   **Text Extraction:** Backend extracts text content from PDFs.
*   **Vector Indexing:** Document text is chunked, embedded, and indexed into a persistent ChromaDB vector store for efficient similarity search.
*   **Conversational Q&A:** Users can ask questions about an uploaded document.
    *   Utilizes LangChain and the Gemini language model.
    *   Supports conversational context (remembers previous turns in the chat for a selected document).
    *   Retrieval Augmented Generation (RAG) pattern to ground answers in document content.
*   **Document Management:** Users can select from previously uploaded documents to chat with.
*   **Modern UI:**
    *   Built with React, Tailwind CSS, and Framer Motion for a responsive and animated user experience.
    *   Clear interface for uploading, selecting documents, and chatting.
*   **Scalable Backend:**
    *   Built with FastAPI for high performance.
    *   Asynchronous processing for PDF indexing using background tasks.

## Tech Stack

**Backend:**

*   **Framework:** FastAPI
*   **NLP/LLM Orchestration:** LangChain
    *   **LLM:** Google Gemini Pro (via `langchain-google-genai`)
    *   **Embeddings:** Google Generative AI Embeddings (e.g., `models/embedding-001`)
    *   **Text Splitting:** `RecursiveCharacterTextSplitter`
    *   **Vector Store:** ChromaDB (persistent)
    *   **Conversational Logic:** LangGraph for stateful conversation and memory management
*   **PDF Parsing:** PyMuPDF (fitz)
*   **Database (Metadata):** SQLite (via SQLAlchemy)
*   **Environment Management:** `uv` (or `pip` with `venv`)
*   **Server:** Uvicorn

**Frontend:**

*   **Framework:** React (Vite or Create React App)
*   **Styling:** Tailwind CSS
*   **Animation:** Framer Motion
*   **API Client:** Axios
*   **State Management:** React Context API / `useState`

## Project Structure

```
.
├── backend/
│   ├── app/                    # Main FastAPI application code
│   │   ├── crud/               # Database CRUD operations
│   │   ├── db/                 # Database setup (SQLAlchemy)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── routers/            # API endpoint definitions
│   │   ├── schemas/            # Pydantic data validation models
│   │   ├── services/           # Business logic (Q&A service)
│   │   ├── utils/              # Utility functions (PDF parsing)
│   │   └── vector_store/       # ChromaDB integration
│   ├── uploaded_pdfs/          # Stores uploaded PDF files (not available in GitHub)
│   ├── extracted_texts/        # Stores extracted text from PDFs (optional, for debugging or will be used later) (not available in GitHub)
│   ├── chroma_db_data/         # Persistent data for ChromaDB (not available in GitHub)
│   ├── .env                    # Environment variables for backend
│   ├── requirements.txt        # Backend Python dependencies
│   └── run.py                  # Script to run the backend server
├── frontend/
│   ├── public/                 # Public assets for React app, SVGs and PNGs downloaded from figma file 
│   ├── src/
│   │   ├── assets/             
│   │   ├── components/         # React components (UI, layout, chat, etc.)
│   │   ├── pages/              # Top-level page components
│   │   ├── services/           # API client (api.js)
│   │   ├── App.jsx             
|   |   ├── index.css           # for tailwind configurations and themeing(v4)
│   │   └── main.jsx            # (or index.js)
│   ├── .env                    # Environment variables for frontend
│   └── package.json
└── README.md
```

## Getting Started

### Prerequisites

*   Python 3.11
*   Node.js 16+ and npm/yarn (or `uv` for Python environment if you prefer)
*   Access to Google Gemini API (and a `GOOGLE_API_KEY`)

### Backend Setup

1.  **Navigate to the `backend` directory:**
    ```bash
    cd backend
    ```

2.  **Create and activate a virtual environment:**
    *   Using `venv`:
        ```bash
        python -m venv venv
        source venv/bin/activate  # macOS/Linux
        # venv\Scripts\activate    # Windows
        ```
    *   Using `uv` (if you installed it globally):
        ```bash
        uv venv
        source .venv/bin/activate # macOS/Linux
        # .venv\Scripts\activate   # Windows
        ```

3.  **Install Python dependencies:**
    *   Using `pip`:
        ```bash
        pip install -r requirements.txt
        ```
    *   Using `uv`:
        ```bash
        uv pip install -r requirements.txt
        ```
    *(Ensure `requirements.txt` is up-to-date with all necessary packages like `fastapi`, `uvicorn`, `langchain`, `langchain-google-genai`, `langchain-community`, `langgraph`, `pymupdf`, `sqlalchemy`, `python-dotenv`, `chromadb`, `axios` [if testing backend directly sometimes], `python-multipart`)*

4.  **Set up environment variables:**
    Create a `.env` file in the `backend` directory:
    ```env
    # backend/.env
    DATABASE_URL="sqlite:///./pdf_qna_app.db"
    GOOGLE_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
    # Add any other necessary backend environment variables
    ```
    Replace `YOUR_GOOGLE_GEMINI_API_KEY` with your actual key.

5.  **Run the backend server:**
    ```bash
    python run.py
    # or if using uv directly for running scripts:
    # uv run run.py
    ```
    The backend API should now be running, typically at `http://localhost:8000`. You can access the OpenAPI docs at `http://localhost:8000/docs`.

### Frontend Setup

1.  **Navigate to the `frontend` directory:**
    ```bash
    cd ../frontend  # Assuming you are in the backend directory
    ```

2.  **Install Node.js dependencies:**
    ```bash
    npm install
    # or
    # yarn install
    ```

3.  **Set up environment variables (optional but recommended):**
    Create a `.env` file in the `frontend` directory:
    ```env
    # frontend/.env
    REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
    ```
    This tells the frontend where the backend API is located.

4.  **Run the frontend development server:**
    ```bash
    npm start
    # or
    # yarn start
    ```
    The React application should open in your browser, typically at `http://localhost:3000`.

## API Endpoints (Backend)

*   **`POST /api/v1/documents/upload`**: Upload a PDF file.
    *   Request: `multipart/form-data` with a `file` field.
    *   Response: JSON object with uploaded document metadata.
*   **`GET /api/v1/documents/`**: List all uploaded documents.
    *   Response: JSON array of document metadata.
*   **`GET /api/v1/documents/{document_id}`**: Get details for a specific document.
    *   Response: JSON object with document metadata.
*   **`POST /api/v1/documents/{document_id}/ask`**: Ask a question about a specific document.
    *   Request Body (JSON):
        ```json
        {
          "question": "Your question here",
          "chat_history": [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
          ]
        }
        ```
    *   Response Body (JSON):
        ```json
        {
          "answer": "The AI's answer"
        }
        ```

## Architecture Overview

1.  **Frontend (React):**
    *   Handles user interactions (file uploads, question input).
    *   Manages UI state (current document, chat history).
    *   Communicates with the backend API via Axios.
2.  **Backend (FastAPI):**
    *   **Upload:** Receives PDF, saves it, extracts text, and triggers background indexing.
    *   **Indexing (Background Task with LangChain & ChromaDB):**
        1.  Text from PDF is chunked.
        2.  Chunks are converted to embeddings using Google's embedding model.
        3.  Chunks and embeddings are stored in a persistent ChromaDB collection specific to the document.
    *   **Q&A (LangGraph & LangChain):**
        1.  User question and chat history are received.
        2.  A LangGraph application manages the conversational state.
        3.  Relevant context chunks are retrieved from ChromaDB based on the current question (and condensed history).
        4.  The retrieved context, original question, and chat history are passed to the Gemini LLM to generate an answer.
        5.  The answer is returned to the frontend.
    *   **Database (SQLite):** Stores metadata about uploaded PDFs.

## Future Enhancements (Optional)
*   Saving chats history in
*   User authentication and authorization.
*   Support for more document types (e.g., .docx, .txt).
*   Streaming LLM responses for better UX.
*   More advanced document management (delete, rename).
*   Option to choose different LLM models or embedding models.
*   More sophisticated error handling and notifications.
*   Unit and integration tests.
*   Deployment to a cloud platform (e.g., AWS, Google Cloud, Vercel/Netlify).

---
