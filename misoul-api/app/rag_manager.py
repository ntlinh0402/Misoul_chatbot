# app/rag_manager.py
from app.pdf_processor_langchain import PDFProcessor

class RAGManager:
    """
    Quản lý tìm kiếm và truy xuất thông tin từ Vector Database.
    
    Lớp này tìm kiếm tài liệu liên quan đến truy vấn của người dùng,
    kết hợp với phân tích cảm xúc để cung cấp thông tin chính xác và phù hợp.
    """
    
    def __init__(self, vector_db=None):
        """
        Khởi tạo RAGManager với vector database
        
        Args:
            vector_db: Vector database (FAISS hoặc None)
        """
        # Nếu không cung cấp vector_db, tải từ đĩa
        self.vector_db = vector_db or PDFProcessor.load_vector_store()
        print("✅ Đã khởi tạo RAG Manager thành công!")
        
    def retrieve_documents(self, query, emotional_level=1, top_k=3):

        if self.vector_db is None:
            print("⚠️ Vector database không có sẵn, trả về danh sách tài liệu trống")
            return []
        
    # Tiếp tục xử lý nếu có vector_db...

        expanded_query = self._expand_query(query, emotional_level)
        
        # Tìm kiếm tài liệu tương tự
        try:
            if self.vector_db:
                documents = self.vector_db.similarity_search(expanded_query, k=top_k)
                print(f"🔍 Đã tìm thấy {len(documents)} tài liệu liên quan")
                for i, doc in enumerate(documents):
                    category = doc.metadata.get('category', 'không rõ')
                    print(f"  Tài liệu {i+1}: {category} - {doc.page_content[:50]}...")
                return documents
            else:
                print("⚠️ Vector database chưa được khởi tạo")
                return []
        except Exception as e:
            print(f"⚠️ Lỗi khi tìm kiếm tài liệu: {e}")
            return []
    
    def _expand_query(self, query, emotional_level):
        """
        Mở rộng truy vấn dựa trên mức độ cảm xúc
        
        Args:
            query: Truy vấn gốc
            emotional_level: Mức độ cảm xúc (1-5)
            
        Returns:
            str: Truy vấn đã mở rộng
        """
        # Các từ khóa liên quan đến mỗi mức độ cảm xúc
        emotional_keywords = {
            1: ["bình thường", "ổn định", "tích cực"],
            2: ["lo lắng nhẹ", "căng thẳng nhẹ", "hơi buồn"],
            3: ["lo âu", "căng thẳng", "buồn", "trầm"],
            4: ["trầm cảm", "lo âu nặng", "căng thẳng cao", "sợ hãi"],
            5: ["khủng hoảng", "tuyệt vọng", "cực kỳ lo âu", "cực kỳ trầm cảm"]
        }
        
        # Lấy từ khóa phù hợp với mức độ cảm xúc
        keywords = emotional_keywords.get(emotional_level, emotional_keywords[1])
        
        # Mở rộng truy vấn với các từ khóa
        expanded_query = f"{query} {' '.join(keywords)}"
        
        return expanded_query