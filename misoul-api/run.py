import os
from app.api import app
from config import Config  # Thêm dòng này để import Config

if __name__ == '__main__':
    # Kiểm tra API key
    if not Config.GOOGLE_API_KEY:
        print("⚠️ CẢNH BÁO: GOOGLE_API_KEY chưa được thiết lập!")
        print("Vui lòng thiết lập API key trong file .env hoặc biến môi trường.")
    
    # In thông tin về đường dẫn để debug
    print(f"Thư mục hiện tại: {os.getcwd()}")
    print(f"Đường dẫn vector database từ config: {Config.VECTOR_DB_PATH}")
    print(f"Đường dẫn vector database tồn tại: {os.path.exists(Config.VECTOR_DB_PATH)}")
    
    # Kiểm tra vector database
    if not os.path.exists(Config.VECTOR_DB_PATH):
        print(f"⚠️ CẢNH BÁO: Không tìm thấy vector database tại {Config.VECTOR_DB_PATH}")
        print("Vui lòng đảm bảo vector database đã được tạo.")
    
    # Chạy Flask app trong chế độ debug nếu được cấu hình
    debug_mode = Config.DEBUG
    print(f"🚀 Khởi động MISOUL API trong chế độ {'DEBUG' if debug_mode else 'PRODUCTION'}")
    
    # Chạy app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)