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

# Biến global để lưu trữ instance chatbot và kiểm soát xử lý PDF
misoul_chatbot = None
PDF_PROCESSED = False

def get_misoul_instance():
    """
    Khởi tạo một instance MISOUL Chatbot (nếu chưa có) và trả về nó
    """
    global misoul_chatbot, PDF_PROCESSED
    
    if misoul_chatbot is None:
        try:
            app.logger.info("Khởi tạo MISOUL Chatbot...")
            
            # Thay thế QdrantManager bằng FAISS
            from app.pdf_processor_langchain import PDFProcessor
            PDF_PROCESSED = PDFProcessor.check_processing_status()

            # Tải vector store
            vector_db = PDFProcessor.load_vector_store()
            
            if vector_db is None and not PDF_PROCESSED:
                app.logger.warning("Không tìm thấy vector database. Kiểm tra thư mục vectorstore/db_faiss")
                app.logger.info("Tạo vector database từ file PDF có sẵn...")
                processor = PDFProcessor()
                success = processor.process_all_pdfs()
                PDF_PROCESSED = True  # Đánh dấu đã xử lý, ngay cả khi thất bại
                
                if success:
                    vector_db = PDFProcessor.load_vector_store()
                else:
                    app.logger.error("Không thể xử lý PDF và tạo vector database")
                    # Trả về None nếu không thể khởi tạo vector database
                    return None
            #elif vector_db is None:
             #   app.logger.warning("Không tìm thấy vector database và đã thử xử lý PDF trước đó")
                # Tiếp tục mà không cần vector database
            
            # Khởi tạo các thành phần
            llm_manager = GeminiManager(model_name=Config.MODEL_NAME)
            rag_manager = RAGManager(vector_db=vector_db)
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
    if request.endpoint == 'health_check' or request.endpoint == 'list_routes':
        return  # Không yêu cầu API key cho health check và list routes
    
    # Xử lý OPTIONS request cho CORS
    if request.method == 'OPTIONS':
        return
    
    # Lấy API key từ header
    auth_header = request.headers.get('Authorization')
    
    # Kiểm tra API key
    if Config.MISOUL_API_KEY and Config.MISOUL_API_KEY != "misoul_test_key":
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Thiếu Authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        if token != Config.MISOUL_API_KEY:
            return jsonify({"error": "API key không hợp lệ"}), 401

# Hàm xử lý phản hồi của chatbot
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
@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    """
    Kiểm tra trạng thái hoạt động của API
    """
    if request.method == 'OPTIONS':
        return '', 200
        
    return jsonify({
        "status": "healthy",
        "message": "MISOUL API đang hoạt động bình thường",
        "version": "1.0.0"
    })

# Route chính để trò chuyện với MISOUL
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    """
    Endpoint chính để tương tác với MISOUL Chatbot
    """
    # Xử lý request OPTIONS cho CORS
    if request.method == 'OPTIONS':
        return '', 200
    
    # Kiểm tra API key
    auth_result = verify_api_key()
    if auth_result:
        return auth_result
    
    try:
        # Ghi nhận thời gian bắt đầu
        start_time = time.time()
        
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
        
        # Kiểm tra nếu misoul là None
        if misoul is None:
            return jsonify({"error": "Không thể khởi tạo MISOUL Chatbot"}), 500
        
        # Kiểm tra thời gian xử lý
        if time.time() - start_time > 10:  # 10 giây timeout cho khởi tạo
            return jsonify({"error": "Thời gian khởi tạo MISOUL quá lâu"}), 504
        
        # Xử lý tin nhắn với MISOUL
        try:
            with_timeout = True  # Đặt timeout cho xử lý tin nhắn
            timeout_seconds = 30  # 30 giây timeout
            
            if with_timeout:
                import threading
                import queue
                
                result_queue = queue.Queue()
                
                def process_with_queue():
                    try:
                        result = misoul.process_message(message, emotional_level, biometric_data, user_id)
                        result_queue.put(("success", result))
                    except Exception as e:
                        result_queue.put(("error", str(e)))
                
                # Tạo và bắt đầu thread
                thread = threading.Thread(target=process_with_queue)
                thread.daemon = True
                thread.start()
                
                # Chờ kết quả với timeout
                try:
                    status, response = result_queue.get(timeout=timeout_seconds)
                    
                    if status == "error":
                        raise Exception(response)
                    
                except queue.Empty:
                    return jsonify({"error": f"Xử lý tin nhắn quá thời gian ({timeout_seconds}s)"}), 504
            else:
                # Xử lý thông thường không có timeout
                response = misoul.process_message(message, emotional_level, biometric_data, user_id)
            
        except Exception as e:
            app.logger.error(f"Lỗi khi xử lý tin nhắn: {str(e)}")
            return jsonify({"error": f"Lỗi khi xử lý tin nhắn: {str(e)}"}), 500
        
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
@app.route('/api/clear_history', methods=['POST', 'OPTIONS'])
def clear_history():
    """
    Xóa lịch sử trò chuyện của một người dùng
    """
    # Xử lý request OPTIONS cho CORS
    if request.method == 'OPTIONS':
        return '', 200
        
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
@app.route('/api/save_history', methods=['POST', 'OPTIONS'])
def save_history():
    """
    Lưu lịch sử trò chuyện của một người dùng vào file
    """
    # Xử lý request OPTIONS cho CORS
    if request.method == 'OPTIONS':
        return '', 200
        
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

# Route để liệt kê tất cả các routes
@app.route('/api/routes', methods=['GET', 'OPTIONS'])
def list_routes():
    """
    Liệt kê tất cả các routes trong ứng dụng
    """
    if request.method == 'OPTIONS':
        return '', 200
        
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "rule": str(rule)
        })
    return jsonify(routes)