import os
import shutil
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from werkzeug.utils import secure_filename
import uvicorn

from config import settings
from models.schemas import (
    ChatRequest, 
    ChatResponse, 
    UploadResponse, 
    ErrorResponse,
    HealthResponse
)
from services.pdf_processor import PDFProcessor
from services.ai_service import AIService

# Initialize services
pdf_processor = PDFProcessor()
ai_service = AIService(api_key=settings.GOOGLE_API_KEY)

# Store document content in memory (in production, use a database or Redis)
document_store = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    print("=" * 50)
    print("AI Document Q&A API Starting...")
    print(f"Upload directory: {settings.UPLOAD_DIR}")
    print(f"Max file size: {settings.MAX_FILE_SIZE / (1024*1024)}MB")
    print(f"Server running on http://{settings.HOST}:{settings.PORT}")
    print("=" * 50)
    
    # Validate API key
    if ai_service.validate_api_key():
        print("✓ Google Gemini API key is valid")
    else:
        print("✗ Warning: Google Gemini API key validation failed")
    
    yield
    
    # Shutdown
    print("Shutting down AI Document Q&A API...")
    
    # Clean up all uploaded files
    for session_id in list(document_store.keys()):
        filepath = document_store[session_id]['filepath']
        if os.path.exists(filepath):
            os.remove(filepath)
    
    document_store.clear()
    print("Cleanup completed")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="AI Document Q&A API",
    description="Backend API for AI-powered document question answering",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in settings.ALLOWED_EXTENSIONS


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return {
        "status": "healthy",
        "message": "AI Document Q&A API is running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Server is running"
    }


@app.post("/upload", response_model=UploadResponse, status_code=status.HTTP_200_OK)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a PDF document for processing.
    
    Args:
        file: PDF file upload
        
    Returns:
        Upload confirmation with session ID
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file selected"
            )
        
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(settings.UPLOAD_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(file_content)
        
        # Process PDF
        try:
            text_content = pdf_processor.extract_text(filepath)
        except Exception as e:
            # Clean up file if processing fails
            if os.path.exists(filepath):
                os.remove(filepath)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not extract text from PDF: {str(e)}"
            )
        
        if not text_content or len(text_content.strip()) < 10:
            # Clean up file if no content
            if os.path.exists(filepath):
                os.remove(filepath)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract meaningful text from PDF. The file may be scanned or corrupted."
            )
        
        # Store document content with session ID
        session_id = os.path.basename(filename)
        document_store[session_id] = {
            'content': text_content,
            'filename': filename,
            'chunks': pdf_processor.chunk_text(text_content),
            'filepath': filepath
        }
        
        return UploadResponse(
            message="File uploaded successfully",
            session_id=session_id,
            filename=filename,
            content_length=len(text_content)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest):
    """
    Send a question about the uploaded document.
    
    Args:
        request: Chat request containing message and session_id
        
    Returns:
        AI-generated response
    """
    try:
        # Validate session
        if request.session_id not in document_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found. Please upload a document first."
            )
        
        # Get document content
        document_data = document_store[request.session_id]
        document_content = document_data['content']
        
        # Check if document is too large, use chunking
        if len(document_content) > 10000:  # If document is large
            chunks = document_data['chunks']
            relevant_chunks = pdf_processor.find_relevant_chunks(chunks, request.message, top_k=3)
            
            if relevant_chunks:
                response_text = ai_service.get_answer_with_chunks(request.message, relevant_chunks)
            else:
                # Fallback to full document
                response_text = ai_service.get_answer(request.message, document_content)
        else:
            # Use full document for smaller documents
            response_text = ai_service.get_answer(request.message, document_content)
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your question: {str(e)}"
        )


@app.delete("/clear/{session_id}", status_code=status.HTTP_200_OK)
async def clear_session(session_id: str):
    """
    Clear session and delete uploaded file.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success message
    """
    try:
        if session_id in document_store:
            # Delete uploaded file
            filepath = document_store[session_id]['filepath']
            if os.path.exists(filepath):
                os.remove(filepath)
            
            # Remove from store
            del document_store[session_id]
            
            return {"message": "Session cleared successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@app.get("/sessions", status_code=status.HTTP_200_OK)
async def list_sessions():
    """
    List all active sessions.
    
    Returns:
        List of active session IDs
    """
    return {
        "sessions": list(document_store.keys()),
        "count": len(document_store)
    }


# Exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )