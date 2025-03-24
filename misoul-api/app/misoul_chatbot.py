# Thêm vào file misoul_chatbot.py
import re
class MISOULChatbot:
    """
    MISOUL Chatbot - Người bạn tâm giao với chuyên môn tâm lý
    """
    
    def __init__(self, llm_manager, rag_manager, prompt_manager):
        # Các thuộc tính hiện tại
        self.llm_manager = llm_manager
        self.rag_manager = rag_manager
        self.prompt_manager = prompt_manager
        self.conversation_memory = {}  # Lưu trữ cuộc trò chuyện theo ID người dùng
        self.pending_responses = {}    # Lưu trữ phản hồi đang chờ xác nhận
        self.waiting_confirmation = {} # Theo dõi trạng thái chờ xác nhận
        
        # Thêm thuộc tính mới để quản lý cảnh báo
        self.warning_shown = {}        # Theo dõi người dùng đã được hiển thị cảnh báo hay chưa
        self.self_harm_messages = []   # Danh sách từ khóa liên quan đến tự hại
        self.initialize_self_harm_keywords()
        
        print("✅ Đã khởi tạo MISOUL Chatbot thành công!")
    
    def initialize_self_harm_keywords(self):
        """Khởi tạo danh sách từ khóa liên quan đến tự hại"""
        self.self_harm_messages = [
            "tự tử", "kết thúc cuộc sống", "kết thúc cuộc đời", "chết", "không muốn sống", 
            "không còn muốn sống", "tôi chết", "tự hại", "tự làm đau", "cắt tay", 
            "uống thuốc", "nhảy lầu", "treo cổ", "kết liễu", "tự giết"
        ]
    
    def check_self_harm_content(self, message):
        """
        Kiểm tra nội dung có liên quan đến tự hại hay không
        
        Args:
            message: Tin nhắn của người dùng
            
        Returns:
            bool: True nếu phát hiện nội dung tự hại, False nếu không
        """
        message = message.lower()
        for keyword in self.self_harm_messages:
            if keyword in message:
                return True
        return False
    
    def get_emergency_warning(self):
        """
        Tạo cảnh báo khẩn cấp khi phát hiện nội dung tự hại
        
        Returns:
            str: Chuỗi cảnh báo
        """
        return ("**KHẨN CẤP! Nếu bạn đang có ý định tự gây hại cho bản thân, "
                "vui lòng gọi ngay đến một trong các số điện thoại sau:**\n"
                "* **Tổng đài tư vấn tâm lý miễn phí: 1800-8440**\n"
                "* **Hotline Tư vấn và can thiệp cho người có ý định tự tử: 1800-8440**\n"
                "* **Trung tâm Sức khỏe Tâm thần Bạch Mai: (024) 3825.3028**\n"
                "* **Cứu thương: 115**")
    
    def should_show_warning(self, user_message, user_id):
        """
        Kiểm tra xem có nên hiển thị cảnh báo khẩn cấp không
        
        Args:
            user_message: Tin nhắn của người dùng
            user_id: ID của người dùng
            
        Returns:
            bool: True nếu nên hiển thị cảnh báo, False nếu không
        """
        # Kiểm tra nội dung tự hại
        contains_self_harm = self.check_self_harm_content(user_message)
        
        # Kiểm tra tin nhắn trước đó có từ chối ý định tự hại không
        denied_self_harm_intent = False
        if user_id in self.conversation_memory and self.conversation_memory[user_id]:
            last_messages = self.conversation_memory[user_id][-3:]  # Lấy 3 tin nhắn gần nhất
            for msg, _ in last_messages:
                # Kiểm tra nếu người dùng đã từ chối ý định tự hại
                if "không có ý định tự hại" in msg.lower() or "không tự hại" in msg.lower():
                    denied_self_harm_intent = True
        
        # Kiểm tra xem đã hiển thị cảnh báo trong 5 tin nhắn gần đây chưa
        warning_recently_shown = False
        if user_id in self.warning_shown:
            last_shown = self.warning_shown.get(user_id, 0)
            warning_recently_shown = (len(self.conversation_memory.get(user_id, [])) - last_shown) < 5
        
        # Quyết định hiển thị cảnh báo
        show_warning = contains_self_harm and not denied_self_harm_intent and not warning_recently_shown
        
        # Cập nhật trạng thái hiển thị cảnh báo
        if show_warning:
            self.warning_shown[user_id] = len(self.conversation_memory.get(user_id, []))
        
        return show_warning
    
    def modify_prompt_guidelines(self, emotional_level):
        """
        Tạo hướng dẫn cho mô hình dựa trên mức độ cảm xúc
        
        Args:
            emotional_level: Mức độ cảm xúc (1-5)
            
        Returns:
            str: Hướng dẫn bổ sung cho prompt
        """
        guidelines = [
            "Hãy tạo phản hồi theo các hướng dẫn sau:",
            "1. KHÔNG nhắc đến các chỉ số cụ thể như nhịp tim, HRV, chất lượng giấc ngủ trong tin nhắn.",
            "2. Thay vì đề cập đến các chỉ số, hãy tóm tắt trạng thái chung của người dùng (ví dụ: 'Tôi cảm nhận được bạn đang căng thẳng' thay vì 'Nhịp tim của bạn là 90 BPM').",
            "3. Chia nhỏ câu trả lời thành các đoạn hoàn chỉnh, tránh cắt giữa câu.",
            "4. Giữ nguyên định dạng viết hoa/thường và dấu câu.",
            "5. Khi được xác nhận 'có, tôi muốn', hãy đảm bảo nối tiếp lời khuyên một cách liền mạch, không lặp lại."
        ]
        
        # Bổ sung hướng dẫn dựa trên mức độ cảm xúc
        if emotional_level >= 4:
            guidelines.append("6. Người dùng đang ở trạng thái cảm xúc rất căng thẳng. Hãy sử dụng ngôn ngữ nhẹ nhàng, rõ ràng và đưa ra các hướng dẫn cụ thể từng bước.")
        elif emotional_level == 3:
            guidelines.append("6. Người dùng đang ở trạng thái lo âu vừa phải. Hãy thể hiện sự đồng cảm và cung cấp các phương pháp giảm căng thẳng.")
        else:
            guidelines.append("6. Hãy duy trì giọng điệu thân thiện, cởi mở và hỗ trợ.")
            
        return "\n".join(guidelines)
    
    def split_response_into_messages(self, response):
        """
        Chia phản hồi dài thành nhiều tin nhắn ngắn hơn, đảm bảo không cắt giữa câu
        
        Args:
            response: Phản hồi gốc từ mô hình
            
        Returns:
            list: Danh sách các tin nhắn nhỏ hơn
        """
        # Trường hợp 1: Chia theo đoạn văn rõ ràng
        if '\n\n' in response:
            messages = [msg.strip() for msg in response.split('\n\n') if msg.strip()]
            return messages
        
        # Trường hợp 2: Chia theo dấu chấm câu nhưng đảm bảo câu hoàn chỉnh
        sentences = []
        current = ""
        
        # Tách theo câu một cách thông minh
        parts = []
        # Chia theo các dấu chấm câu kết thúc
        for part in re.split(r'(?<=[.!?])\s+', response):
            if not part.strip():
                continue
            parts.append(part)
        
        # Gom các câu thành đoạn hợp lý
        for part in parts:
            # Nếu câu hiện tại đã đủ dài, bắt đầu đoạn mới
            if len(current) > 200 or (current and '\n' in part):  # Tăng độ dài từ 100 lên 200
                sentences.append(current.strip())
                current = part
            else:
                current += " " + part if current else part
                
        # Thêm đoạn cuối cùng nếu còn
        if current:
            sentences.append(current.strip())
        
        # Thêm bước xử lý đặc biệt cho các danh sách
        result = []
        for sentence in sentences:
            # Xử lý danh sách đặc biệt
            if ("\n- " in sentence or "\n1. " in sentence or "\n2. " in sentence or 
                ":\n-" in sentence or ":\n1." in sentence or ":\n2." in sentence):
                # Tách phần giới thiệu và danh sách
                parts = re.split(r'((?:\n|:)\s*(?:-|\d+\.)\s+)', sentence, 1)
                if len(parts) > 1:
                    intro = parts[0].strip()
                    if intro:
                        result.append(intro)
                    
                    # Xử lý phần danh sách
                    list_content = sentence[len(intro):].strip()
                    # Tách danh sách thành từng mục
                    list_items = re.split(r'\n\s*(?:-|\d+\.)\s+', list_content)
                    for item in list_items:
                        if item.strip():
                            result.append(f"- {item.strip()}")
                else:
                    result.append(sentence)
            else:
                result.append(sentence)
        
        return result
    
    def detect_exercise_suggestion(self, response):
        """
        Kiểm tra xem phản hồi có chứa bài tập/hướng dẫn không và tách phần giới thiệu và hướng dẫn
        
        Args:
            response: Phản hồi từ mô hình
            
        Returns:
            dict: Thông tin về việc có cần xin phép hay không
        """
        # Kiểm tra xem có phải là câu trả lời đề xuất bài tập không
        exercise_indicators = [
            "bài tập", "hướng dẫn", "các bước", "phương pháp",
            "thực hành", "kỹ thuật", "tập luyện", "gợi ý", "5-4-3-2-1",
            "kỹ thuật thở", "thiền", "thư giãn", "nghỉ ngơi"
        ]
        
        contains_exercise = any(indicator in response.lower() for indicator in exercise_indicators)
        
        if contains_exercise:
            # Tìm vị trí thích hợp để chia phản hồi
            # Cải tiến: Tìm câu hoàn chỉnh cuối cùng trước phần hướng dẫn
            sentences = re.split(r'(?<=[.!?])\s+', response)
            intro_sentences = []
            exercise_sentences = []
            
            found_exercise = False
            for sentence in sentences:
                if not found_exercise:
                    # Kiểm tra xem câu này có chứa indicator không
                    if any(indicator in sentence.lower() for indicator in exercise_indicators):
                        # Tìm điểm phân chia phù hợp
                        for indicator in exercise_indicators:
                            if indicator in sentence.lower():
                                pattern = re.compile(re.escape(indicator), re.IGNORECASE)
                                parts = pattern.split(sentence, 1)
                                if len(parts) > 1:
                                    # Thêm phần đầu vào intro nếu có
                                    if parts[0].strip():
                                        intro_sentences.append(parts[0].strip())
                                    # Thêm phần sau vào exercise
                                    exercise_text = indicator + parts[1].strip()
                                    exercise_sentences.append(exercise_text)
                                    found_exercise = True
                                    break
                        
                        # Nếu không tìm được điểm phân chia, thêm toàn bộ câu vào exercise
                        if not found_exercise:
                            exercise_sentences.append(sentence)
                            found_exercise = True
                    else:
                        intro_sentences.append(sentence)
                else:
                    exercise_sentences.append(sentence)
            
            # Tạo nội dung giới thiệu và hướng dẫn
            intro_text = " ".join(intro_sentences).strip()
            exercise_text = " ".join(exercise_sentences).strip()
            
            # Thêm câu hỏi xin phép
            permission_message = f"{intro_text} Bạn có muốn tôi chia sẻ một số bài tập/hướng dẫn có thể giúp ích không?"
            
            return {
                "requires_permission": True,
                "initial_message": permission_message,
                "full_content": exercise_text
            }
        
        return {
            "requires_permission": False,
            "initial_message": "",
            "full_content": response
        }
    
    def process_message(self, user_message, emotional_level=1, biometric_data=None, user_id="default_user"):
        """
        Xử lý tin nhắn người dùng và tạo phản hồi với bộ nhớ cuộc trò chuyện
        
        Args:
            user_message: Tin nhắn của người dùng
            emotional_level: Mức độ cảm xúc (1-5)
            biometric_data: Dữ liệu sinh trắc học (tùy chọn)
            user_id: ID của người dùng để lưu trữ cuộc trò chuyện riêng (mặc định: "default_user")
                
        Returns:
            str hoặc dict: Phản hồi từ chatbot (tương thích ngược với API hiện tại)
        """
        # Kiểm tra nếu đang chờ xác nhận từ người dùng
        if user_id in self.waiting_confirmation and self.waiting_confirmation[user_id]:
            # Kiểm tra phản hồi của người dùng
            positive_responses = ["có", "ừ", "đồng ý", "ok", "được", "vâng", "yes", "y", "👍", "okk"]
            
            if any(pos in user_message.lower() for pos in positive_responses):
                # Người dùng đồng ý, gửi nội dung hướng dẫn đã được chia nhỏ
                pending_content = self.pending_responses.get(user_id, "")
                messages = self.split_response_into_messages(pending_content)
                
                # Cập nhật lịch sử trò chuyện
                conversation_history = self.conversation_memory.get(user_id, [])
                conversation_history.append((user_message, pending_content))
                
                # Giới hạn lịch sử để tránh prompt quá dài
                max_history_length = 10
                if len(conversation_history) > max_history_length:
                    conversation_history = conversation_history[-max_history_length:]
                
                # Lưu lịch sử trò chuyện đã cập nhật
                self.conversation_memory[user_id] = conversation_history
                
                # Đặt lại trạng thái chờ
                self.waiting_confirmation[user_id] = False
                self.pending_responses[user_id] = ""
                
                # Trả về danh sách tin nhắn (tương thích với API mới)
                return messages
            else:
                # Người dùng từ chối, gửi tin nhắn thay thế
                decline_message = "Không vấn đề. Nếu bạn cần bất kỳ hỗ trợ nào khác, hãy cho tôi biết nhé."
                
                # Cập nhật lịch sử trò chuyện
                conversation_history = self.conversation_memory.get(user_id, [])
                conversation_history.append((user_message, decline_message))
                self.conversation_memory[user_id] = conversation_history
                
                # Đặt lại trạng thái chờ
                self.waiting_confirmation[user_id] = False
                self.pending_responses[user_id] = ""
                
                # Trả về tin nhắn từ chối (tương thích với API mới)
                return decline_message
        
        # Xử lý tin nhắn thông thường
        if not user_message.strip():
            welcome_message = "Xin chào! Tôi là MISOUL, người bạn đồng hành hỗ trợ sức khỏe tâm lý. Tôi có thể giúp gì cho bạn hôm nay?"
            return welcome_message
        
        # Chuẩn bị biometric_data nếu không được cung cấp
        if biometric_data is None:
            biometric_data = {
                'heart_rate': 75 + (emotional_level - 1) * 5,  # 75-95 BPM theo mức độ
                'hrv': 60 - (emotional_level - 1) * 10,        # 60-20 ms theo mức độ
                'sleep_quality': 80 - (emotional_level - 1) * 10  # 80-40% theo mức độ
            }
        
        # Lấy lịch sử trò chuyện của người dùng nếu có
        conversation_history = self.conversation_memory.get(user_id, [])
        
        # Kiểm tra nội dung tự hại và quyết định hiển thị cảnh báo
        show_warning = self.should_show_warning(user_message, user_id)
        
        # Truy xuất tài liệu liên quan
        retrieved_docs = self.rag_manager.retrieve_documents(user_message, emotional_level)
        
        # Thêm hướng dẫn về phản hồi dựa trên mức độ cảm xúc
        guidelines = self.modify_prompt_guidelines(emotional_level)
        
        # Bổ sung hướng dẫn đặc biệt nếu phát hiện nội dung tự hại
        if show_warning:
            guidelines += "\n7. KHÔNG đề cập đến cảnh báo khẩn cấp trong phản hồi, vì thông tin đó sẽ được hiển thị riêng."
            guidelines += "\n8. Thể hiện sự đồng cảm và cung cấp hướng dẫn cụ thể để người dùng tìm kiếm sự giúp đỡ."
        
        # Xây dựng prompt với hướng dẫn bổ sung
        prompt = self.prompt_manager.create_prompt(
            user_message, 
            emotional_level, 
            biometric_data, 
            retrieved_docs, 
            conversation_history,
            guidelines
        )
        
        # Điều chỉnh temperature theo mức độ cảm xúc
        temperature = 0.7
        if emotional_level >= 4:
            temperature = 0.3  # Rất nhất quán khi khủng hoảng
        elif emotional_level == 3:
            temperature = 0.5  # Khá nhất quán khi lo âu vừa phải
        
        # Tạo phản hồi với temperature phù hợp
        response = self.llm_manager.generate_response(prompt, temperature=temperature)
        
        # Tạo cảnh báo nếu cần
        messages = []
        if show_warning:
            messages.append(self.get_emergency_warning())
        
        # Kiểm tra xem có phải phản hồi đề xuất bài tập không
        exercise_info = self.detect_exercise_suggestion(response)
        
        if exercise_info["requires_permission"]:
            # Lưu nội dung đầy đủ để sử dụng sau khi người dùng xác nhận
            self.pending_responses[user_id] = exercise_info["full_content"]
            self.waiting_confirmation[user_id] = True
            
            # Cập nhật lịch sử trò chuyện chỉ với phần giới thiệu
            conversation_history.append((user_message, exercise_info["initial_message"]))
            self.conversation_memory[user_id] = conversation_history
            
            # Thêm tin nhắn xin phép vào danh sách phản hồi
            messages.append(exercise_info["initial_message"])
            
            # Trả về tin nhắn xin phép (tương thích với API mới)
            if len(messages) == 1:
                return messages[0]
            return messages
        else:
            # Chia nhỏ phản hồi thành nhiều tin nhắn
            response_messages = self.split_response_into_messages(response)
            messages.extend(response_messages)
            
            # Cập nhật lịch sử trò chuyện với phản hồi đầy đủ
            conversation_history.append((user_message, response))
            
            # Giới hạn lịch sử để tránh prompt quá dài
            max_history_length = 10
            if len(conversation_history) > max_history_length:
                conversation_history = conversation_history[-max_history_length:]
            
            # Lưu lịch sử trò chuyện đã cập nhật
            self.conversation_memory[user_id] = conversation_history
            
            # Tương thích ngược - trả về danh sách tin nhắn hoặc chuỗi đơn
            if len(messages) == 1:
                return messages[0]  # Trả về chuỗi đơn nếu chỉ có một tin nhắn
            return messages  # Trả về danh sách tin nhắn nếu có nhiều tin nhắn
    
    # [Phần còn lại của class giữ nguyên]
    
    def clear_conversation_history(self, user_id="default_user"):
        """
        Xóa lịch sử trò chuyện của một người dùng cụ thể
        
        Args:
            user_id: ID của người dùng (mặc định: "default_user")
        
        Returns:
            bool: True nếu xóa thành công, False nếu không tìm thấy lịch sử
        """
        if user_id in self.conversation_memory:
            self.conversation_memory[user_id] = []
            self.waiting_confirmation[user_id] = False
            self.pending_responses[user_id] = ""
            return True
        return False
    
    def get_conversation_history(self, user_id="default_user", max_items=None):
        """
        Lấy lịch sử trò chuyện của một người dùng
        
        Args:
            user_id: ID của người dùng (mặc định: "default_user")
            max_items: Số lượng tin nhắn tối đa trả về, None = trả về tất cả
        
        Returns:
            list: Danh sách các cặp (user_message, assistant_response)
        """
        history = self.conversation_memory.get(user_id, [])
        if max_items is not None and max_items > 0:
            return history[-max_items:]
        return history
    
    def save_conversation_history(self, filepath, user_id="default_user"):
        """
        Lưu lịch sử trò chuyện vào file
        
        Args:
            filepath: Đường dẫn file để lưu
            user_id: ID của người dùng (mặc định: "default_user")
        
        Returns:
            bool: True nếu lưu thành công, False nếu có lỗi
        """
        try:
            history = self.conversation_memory.get(user_id, [])
            if not history:
                return False
            
            import json
            from datetime import datetime
            
            data = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "conversation": [
                    {"user": msg, "assistant": resp} for msg, resp in history
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Lỗi khi lưu lịch sử trò chuyện: {e}")
            return False