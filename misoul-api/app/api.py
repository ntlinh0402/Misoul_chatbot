# app/api.py
import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import traceback

# Import config
from config import Config

# Import các module của MISOUL
from app.gemini_manager import GeminiManager
from app.rag_manager import RAGManager
from app.prompt_manager import PromptManager
from app.misoul_chatbot import MISOULChatbot

# Khởi tạo Flask app
app = Flask(__name__)
CORS(app)  # Cho phép Cross-Origin Resource Sharing

# Thiết lập logging
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/misoul_api.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('MISOUL API starting up')

# Cấu hình API key cho Gemini
os.environ["GOOGLE_API_KEY"] = Config.GOOGLE_API_KEY

# Biến global để lưu trữ instance chatbot
misoul_chatbot = None

def get_misoul_instance():
    """
    Khởi tạo một instance MISOUL Chatbot (nếu chưa có) và trả về nó
    """
    global misoul_chatbot
    
    if misoul_chatbot is None:
        try:
            app.logger.info("Khởi tạo MISOUL Chatbot...")
            
            # Khởi tạo QdrantManager
            from app.qdrant_manager import QdrantManager
            
            # Tạo instance
            vectordb = QdrantManager()
            
            # Kiểm tra xem collection có dữ liệu không
            test_docs = vectordb.similarity_search("test", k=1)
            if not test_docs:
                # Thử import từ embedding model
                embedding_model_path = os.path.join(Config.VECTOR_DB_PATH, "embedding_model.pkl")
                if os.path.exists(embedding_model_path):
                    count = vectordb.import_from_embedding_model(embedding_model_path)
                    app.logger.info(f"Đã import {count} tài liệu từ embedding model")
                else:
                    app.logger.warning(f"Không tìm thấy embedding model tại {embedding_model_path}")
            else:
                app.logger.info("Qdrant đã có dữ liệu sẵn sàng sử dụng")

            app.logger.info(f"Đã khởi tạo QdrantManager")
            
            # Khởi tạo các thành phần
            llm_manager = GeminiManager(model_name=Config.MODEL_NAME)
            rag_manager = RAGManager(vector_db=vectordb)
            prompt_manager = PromptManager()
            
            # Khởi tạo chatbot
            misoul_chatbot = MISOULChatbot(llm_manager, rag_manager, prompt_manager)
            app.logger.info("MISOUL Chatbot khởi tạo thành công!")
            
        except Exception as e:
            app.logger.error(f"Lỗi khi khởi tạo MISOUL Chatbot: {str(e)}")
            app.logger.error(traceback.format_exc())
            raise RuntimeError(f"Không thể khởi tạo MISOUL Chatbot: {str(e)}")
    
    return misoul_chatbot

# Kiểm tra API key
def verify_api_key():
    """
    Kiểm tra API key trong header request
    """
    if request.endpoint == 'health_check':
        return  # Không yêu cầu API key cho health check
    
    # Lấy API key từ header
    auth_header = request.headers.get('Authorization')
    
    # Kiểm tra API key
    if Config.MISOUL_API_KEY and Config.MISOUL_API_KEY != "misoul_test_key":
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Thiếu Authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        if token != Config.MISOUL_API_KEY:
            return jsonify({"error": "API key không hợp lệ"}), 401

# Hàm mới: Xử lý phản hồi của chatbot
def process_chatbot_response(response, user_id):
    """
    Xử lý phản hồi từ chatbot và định dạng đúng cho API
    
    Args:
        response: Phản hồi từ chatbot (có thể là chuỗi hoặc danh sách)
        user_id: ID của người dùng
        
    Returns:
        dict: Phản hồi đã định dạng cho API
    """
    # Lấy instance MISOUL
    misoul = get_misoul_instance()
    
    # Kiểm tra xem response có phải là danh sách hay không
    if isinstance(response, list):
        messages = response
    else:
        # Nếu là chuỗi, chuyển về danh sách một phần tử
        messages = [response]
    
    # Kiểm tra xem người dùng có đang chờ xác nhận không
    waiting_confirmation = False
    if hasattr(misoul, 'waiting_confirmation') and user_id in misoul.waiting_confirmation:
        waiting_confirmation = misoul.waiting_confirmation.get(user_id, False)
    
    return {
        "messages": messages,
        "waiting_confirmation": waiting_confirmation
    }

# Route để kiểm tra API đang hoạt động
@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Kiểm tra trạng thái hoạt động của API
    """
    return jsonify({
        "status": "healthy",
        "message": "MISOUL API đang hoạt động bình thường",
        "version": "1.0.0"
    })

# Route chính để trò chuyện với MISOUL
@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Endpoint chính để tương tác với MISOUL Chatbot
    """
    # Kiểm tra API key
    auth_result = verify_api_key()
    if auth_result:
        return auth_result
    
    try:
        # Lấy dữ liệu từ request
        data = request.json
        
        # Kiểm tra các trường bắt buộc
        if not data or 'message' not in data:
            return jsonify({"error": "Thiếu trường 'message' trong request"}), 400
        
        # Lấy thông tin từ request
        message = data.get('message')
        emotional_level = int(data.get('emotional_level', 1))
        user_id = data.get('user_id', 'default_user')
        
        # Kiểm tra giới hạn emotional_level
        if emotional_level < 1 or emotional_level > 5:
            return jsonify({"error": "emotional_level phải từ 1 đến 5"}), 400
        
        # Dữ liệu sinh trắc học (tùy chọn)
        biometric_data = data.get('biometric_data', {
            'heart_rate': 75 + (emotional_level - 1) * 5,
            'hrv': 60 - (emotional_level - 1) * 10,
            'sleep_quality': 80 - (emotional_level - 1) * 10
        })
        
        # Lấy instance MISOUL
        misoul = get_misoul_instance()
        
        # Xử lý tin nhắn với MISOUL
        start_time = time.time()
        response = misoul.process_message(message, emotional_level, biometric_data, user_id)
        processing_time = time.time() - start_time
        
        # Xử lý và định dạng phản hồi
        formatted_response = process_chatbot_response(response, user_id)
        
        # Log thông tin
        app.logger.info(f"Chat request - User: {user_id} | Emotion: {emotional_level} | Time: {processing_time:.2f}s")
        
        # Trả về kết quả
        return jsonify({
            "response": formatted_response,
            "user_id": user_id,
            "emotional_level": emotional_level,
            "processing_time": processing_time
        })
        
    except Exception as e:
        # Xử lý lỗi
        error_message = f"Lỗi khi xử lý yêu cầu: {str(e)}"
        app.logger.error(error_message)
        app.logger.error(traceback.format_exc())
        return jsonify({"error": error_message}), 500

# Route để xóa lịch sử trò chuyện
@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    """
    Xóa lịch sử trò chuyện của một người dùng
    """
    # Kiểm tra API key
    auth_result = verify_api_key()
    if auth_result:
        return auth_result
    
    try:
        data = request.json
        user_id = data.get('user_id', 'default_user')
        
        # Lấy instance MISOUL
        misoul = get_misoul_instance()
        
        # Xóa lịch sử trò chuyện của người dùng
        success = misoul.clear_conversation_history(user_id)
        
        if success:
            app.logger.info(f"Đã xóa lịch sử trò chuyện của user_id: {user_id}")
            return jsonify({"status": "success", "message": f"Đã xóa lịch sử trò chuyện của user_id: {user_id}"})
        else:
            return jsonify({"status": "warning", "message": f"Không tìm thấy lịch sử trò chuyện cho user_id: {user_id}"})
        
    except Exception as e:
        error_message = f"Lỗi khi xóa lịch sử trò chuyện: {str(e)}"
        app.logger.error(error_message)
        app.logger.error(traceback.format_exc())
        return jsonify({"error": error_message}), 500

# Route để lưu lịch sử trò chuyện
@app.route('/api/save_history', methods=['POST'])
def save_history():
    """
    Lưu lịch sử trò chuyện của một người dùng vào file
    """
    # Kiểm tra API key
    auth_result = verify_api_key()
    if auth_result:
        return auth_result
    
    try:
        data = request.json
        user_id = data.get('user_id', 'default_user')
        
        # Tạo thư mục để lưu lịch sử
        history_dir = os.path.join('data', 'conversation_history')
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
        
        # Tạo tên file dựa trên user_id và thời gian
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{user_id}_{timestamp}.json"
        filepath = os.path.join(history_dir, filename)
        
        # Lấy instance MISOUL
        misoul = get_misoul_instance()
        
        # Lưu lịch sử trò chuyện
        
        success = misoul.save_conversation_history(filepath, user_id)
        
        if success:
            app.logger.info(f"Đã lưu lịch sử trò chuyện của user_id: {user_id} vào file: {filepath}")
            return jsonify({
                "status": "success", 
                "message": f"Đã lưu lịch sử trò chuyện thành công",
                "filepath": filepath
            })
        else:
            return jsonify({
                "status": "warning", 
                "message": "Không có lịch sử trò chuyện để lưu hoặc có lỗi khi lưu"
            })
        
    except Exception as e:
        error_message = f"Lỗi khi lưu lịch sử trò chuyện: {str(e)}"
        app.logger.error(error_message)
        app.logger.error(traceback.format_exc())
        return jsonify({"error": error_message}), 500

# Endpoint test đơn giản