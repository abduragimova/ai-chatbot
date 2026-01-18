import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # API Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Server Configuration
    PORT: int = int(os.getenv("PORT", 5001))
    HOST: str = "0.0.0.0"
    
    # File Upload Configuration
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 16777216))  # 16MB
    ALLOWED_EXTENSIONS: set = {"pdf"}
    
    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:8001",
        "http://localhost:3001",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:3001",
    ]
    
    # Create upload directory if it doesn't exist
    @staticmethod
    def create_upload_dir():
        os.makedirs(Settings.UPLOAD_DIR, exist_ok=True)

settings = Settings()
settings.create_upload_dir()