import os
from dotenv import load_dotenv

# Nạp biến môi trường từ file .env (nếu có)
load_dotenv()

class Config:
    # Cấu hình chung
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    MISOUL_API_KEY = os.getenv('MISOUL_API_KEY', 'misoul_test_key')
    
    # Database
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', './app/data/misoul_vectordb')

    # Thêm cấu hình cho Qdrant
    QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'misoul_docs')
    # Model configuration
    MODEL_NAME = os.getenv('MODEL_NAME', 'models/gemini-1.5-flash')