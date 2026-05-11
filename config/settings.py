import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # FastAPI settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit max

    # MongoDB settings
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "aura_ats")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

    # Groq AI settings
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_BASE_URL = "https://api.groq.com/openai/v1"
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-70b-versatile")
    
    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
