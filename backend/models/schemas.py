from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, description="User's question")
    session_id: str = Field(..., min_length=1, description="Session identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is the total budget?",
                "session_id": "document_123.pdf"
            }
        }

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="AI generated response")
    session_id: str = Field(..., description="Session identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "The total budget mentioned in the document is $250,000.",
                "session_id": "document_123.pdf"
            }
        }

class UploadResponse(BaseModel):
    """Response model for file upload"""
    message: str
    session_id: str
    filename: str
    content_length: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "File uploaded successfully",
                "session_id": "document_123.pdf",
                "filename": "document_123.pdf",
                "content_length": 5420
            }
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Document not found",
                "detail": "Please upload a document first"
            }
        }

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "message": "Server is running"
            }
        }