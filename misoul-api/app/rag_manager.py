# app/rag_manager.py
class RAGManager:
    """
    Quản lý tìm kiếm và truy xuất thông tin từ Vector Database.
    
    Lớp này tìm kiếm tài liệu liên quan đến truy vấn của người dùng,
    kết hợp với phân tích cảm xúc để cung cấp thông tin chính xác và phù hợp.
    """
    
    def __init__(self, vector_db):
        """
        Khởi tạo RAGManager với vector database
        
        Args:
            vector_db: Vector database (Chroma)
        """
        self.vector_db = vector_db
        print("✅ Đã khởi tạo RAG Manager thành công!")
        
    def retrieve_documents(self, query, emotional_level=1, top_k=3):
        """
        Truy xuất tài liệu liên quan dựa trên nội dung và trạng thái cảm xúc
        
        Args:
            query: Câu hỏi của người dùng
            emotional_level: Mức độ cảm xúc (1-5)
            top_k: Số lượng tài liệu tối đa trả về
            
        Returns:
            List[Document]: Danh sách tài liệu liên quan
        """
        # Tìm kiếm từ khóa liên quan đến các danh mục
        category_keywords = {
            'anxiety': ['lo âu', 'căng thẳng', 'lo lắng', 'sợ hãi', 'panic', 'hồi hộp', 'khó thở', 'hồi hộp'],
            'depression': ['buồn', 'trầm cảm', 'tuyệt vọng', 'mệt mỏi', 'chán nản', 'cô đơn', 'không vui', 'không muốn'],
            'cbt_techniques': ['suy nghĩ', 'nhận thức', 'hành vi', 'kỹ thuật', 'cbt', 'liệu pháp', 'thay đổi'],
            'mindfulness': ['chánh niệm', 'thiền', 'thư giãn', 'hít thở', 'tập trung', 'ý thức', 'bình tĩnh']
        }
        
        # Xác định danh mục tiềm năng từ truy vấn
        query_lower = query.lower()
        potential_categories = []
        
        for category, keywords in category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                potential_categories.append(category)
        
        # Nếu không tìm thấy danh mục từ từ khóa, sử dụng mức độ cảm xúc để gợi ý
        if not potential_categories:
            if emotional_level >= 4:
                potential_categories = ['depression', 'anxiety']
            elif emotional_level == 3:
                potential_categories = ['anxiety', 'cbt_techniques']
            elif emotional_level == 2:
                potential_categories = ['mindfulness', 'cbt_techniques']
            else:
                potential_categories = ['mindfulness', 'cbt_techniques']
        
        # Tìm kiếm với filter nếu có danh mục
        try:
            results = self.vector_db.similarity_search(query, k=top_k)
            documents = results
            
            # Log kết quả tìm kiếm
            print(f"🔍 Đã tìm thấy {len(documents)} tài liệu liên quan")
            for i, doc in enumerate(documents):
                category = doc.metadata.get('category', 'không rõ') if hasattr(doc, 'metadata') else 'không rõ'
                print(f"  Tài liệu {i+1}: {category} - {doc.page_content[:50]}...")
            
        except Exception as e:
            print(f"⚠️ Lỗi khi tìm kiếm tài liệu: {e}")
            documents = []
        
        return documents