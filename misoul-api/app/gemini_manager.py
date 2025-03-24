# app/gemini_manager.py
import os
import time
import google.generativeai as genai

class GeminiManager:
    """
    Quản lý kết nối và tương tác với Google Gemini API.
    
    Lớp này đóng gói logic gọi API, cấu hình mô hình và xử lý lỗi khi
    tương tác với Google Gemini API.
    """
    
    def __init__(self, model_name="models/gemini-1.5-flash"):
        """
        Khởi tạo GeminiManager với model được chỉ định
        
        Args:
            model_name (str): Tên model Gemini (mặc định: gemini-1.5-flash - nhanh và hiệu quả)
                Lựa chọn khác: models/gemini-1.5-pro (chất lượng cao hơn nhưng chậm hơn)
        """
        self.model_name = model_name
        
        # Kiểm tra API key
        if not os.environ.get("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY chưa được thiết lập, không thể khởi tạo GeminiManager")
        
        # Thiết lập cấu hình generation
        self.generation_config = {
            "temperature": 0.7,        # Độ sáng tạo, cao hơn = sáng tạo hơn
            "top_p": 0.95,             # Sampling với top_p
            "top_k": 64,               # Số lượng tokens có khả năng cao nhất
            "max_output_tokens": 1024, # Độ dài tối đa của output
        }
        
        # Khởi tạo model
        try:
            self.model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=self.generation_config
            )
            print(f"✅ Đã khởi tạo kết nối với Google Gemini API, model: {model_name}")
        except Exception as e:
            print(f"❌ Lỗi khi khởi tạo model: {e}")
            raise ValueError(f"Không thể khởi tạo model {model_name}. Chi tiết lỗi: {str(e)}")
    
    def generate_response(self, prompt, temperature=None, max_tokens=None):
        """
        Tạo phản hồi từ Gemini API với các thông số tùy chỉnh
        
        Args:
            prompt (str): Prompt đầy đủ để gửi tới API
            temperature (float, optional): Độ sáng tạo, từ 0.0-1.0
            max_tokens (int, optional): Số token tối đa trong phản hồi
        
        Returns:
            str: Phản hồi từ Gemini API
        """
        # Cập nhật cấu hình nếu cần
        generation_config = self.generation_config.copy()
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_tokens is not None:
            generation_config["max_output_tokens"] = max_tokens
        
        # Áp dụng cấu hình mới (nếu có)
        if temperature is not None or max_tokens is not None:
            self.model.generation_config = generation_config
        
        # Ghi log cấu hình (cho debug)
        log_config = f"Temperature: {generation_config['temperature']}, Max tokens: {generation_config['max_output_tokens']}"
        
        # Thêm hướng dẫn hệ thống vào prompt thay vì dùng system_instruction
        system_instruction = (
            "Bạn là MISOUL, một người bạn tâm giao với chuyên môn tâm lý sâu sắc, "
            "luôn trả lời bằng tiếng Việt và không lưu trữ dữ liệu người dùng.\n\n"
        )
        enhanced_prompt = system_instruction + prompt
        
        # Gọi API với xử lý lỗi
        try:
            start_time = time.time()
            response = self.model.generate_content(enhanced_prompt)
            end_time = time.time()
            
            # Log thời gian phản hồi
            print(f"⏱️ Thời gian phản hồi: {end_time - start_time:.2f} giây | {log_config}")
            
            return response.text
            
        except Exception as e:
            error_msg = f"Lỗi khi gọi Gemini API: {str(e)}"
            print(f"❌ {error_msg}")
            return f"Xin lỗi, tôi đang gặp khó khăn kỹ thuật. Vui lòng thử lại sau. (Chi tiết: {str(e)[:100]})"