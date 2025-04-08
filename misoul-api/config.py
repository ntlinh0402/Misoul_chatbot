# config.py
import os
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

class Config:
    """
    Cấu hình cho MISOUL API
    """
    # API Keys
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
    MISOUL_API_KEY = os.environ.get('MISOUL_API_KEY', 'misoul_test_key')
    
    # Gemini model
    MODEL_NAME = os.environ.get('MODEL_NAME', 'models/gemini-1.5-flash')
    
    # Đường dẫn lưu trữ vector database
    VECTOR_DB_PATH = os.path.join(os.getcwd(), 'data', 'misoul_vectordb')
    
    # Thêm đường dẫn thư mục PDF
    PDF_DIRECTORY = os.path.join(os.getcwd(), 'data', 'pdfs')
    
    # Cấu hình debug
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'