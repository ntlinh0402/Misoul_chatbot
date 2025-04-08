# app/pdf_processor_langchain.py
import os
import glob
import time
import json
from typing import List, Dict, Any
import traceback
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from config import Config

class MISOULEmbeddings:
    """
    Lớp embeddings tương thích với LangChain
    
    Sử dụng TF-IDF để tạo vector embeddings hiệu quả
    """
    
    def __init__(self, max_features=5000):
        """
        Khởi tạo embedding model
        
        Args:
            max_features: Số lượng tính năng tối đa
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(max_features=max_features)
        self.fitted = False
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Tạo embeddings cho danh sách văn bản
        
        Args:
            texts: Danh sách các văn bản
            
        Returns:
            List[List[float]]: Danh sách các embedding vectors
        """
        # Trích xuất text từ documents nếu đó là đối tượng Document
        if hasattr(texts[0], 'page_content'):
            texts = [doc.page_content for doc in texts]
        
        if not self.fitted:
            self.vectorizer.fit(texts)
            self.fitted = True
        
        embeddings = self.vectorizer.transform(texts).toarray()
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """
        Tạo embedding cho một câu truy vấn
        
        Args:
            text: Câu truy vấn
            
        Returns:
            List[float]: Embedding vector
        """
        if not self.fitted:
            # Nếu chưa fit, thì không thể embed query
            import numpy as np
            return np.zeros(self.vectorizer.max_features).tolist()
        
        embedding = self.vectorizer.transform([text]).toarray()[0]
        return embedding.tolist()

class PDFProcessor:
    """
    Lớp xử lý tài liệu PDF và chuyển đổi thành vector embeddings sử dụng LangChain
    """
    
    def __init__(self, pdf_directory=None, vector_db_path=None):
        """
        Khởi tạo PDFProcessor
        
        Args:
            pdf_directory: Thư mục chứa các file PDF
            vector_db_path: Thư mục lưu trữ vector database
        """
        self.pdf_directory = pdf_directory or Config.PDF_DIRECTORY
        self.vector_db_path = vector_db_path or Config.VECTOR_DB_PATH
        
        # Tạo thư mục nếu chưa tồn tại
        if not os.path.exists(self.pdf_directory):
            os.makedirs(self.pdf_directory)
            print(f"✅ Đã tạo thư mục PDF: {self.pdf_directory}")
            
        if not os.path.exists(self.vector_db_path):
            os.makedirs(self.vector_db_path)
            print(f"✅ Đã tạo thư mục Vector DB: {self.vector_db_path}")
            
        # Khởi tạo embedding model
        self.embedding_model = MISOULEmbeddings()
    
    @staticmethod
    def check_processing_status():
        """Kiểm tra trạng thái đã xử lý PDF"""
        try:
            status_file = os.path.join(Config.VECTOR_DB_PATH, "process_status.json")
            if not os.path.exists(status_file):
                print(f"❌ Không tìm thấy file trạng thái xử lý PDF: {status_file}")
                return False
            
            with open(status_file, 'r') as f:
                import json
                status = json.load(f)
                processed = status.get("processed", False)
                print(f"✅ Đã đọc trạng thái xử lý PDF: {processed}")
                return processed
        except Exception as e:
            print(f"❌ Không thể đọc trạng thái xử lý PDF: {e}")
            return False

    @staticmethod
    def save_processing_status(processed=True):
        """Lưu trạng thái đã xử lý PDF"""
        import time
        import json
        
        try:
            status_file = os.path.join(Config.VECTOR_DB_PATH, "process_status.json")
            # Đảm bảo thư mục tồn tại
            os.makedirs(os.path.dirname(status_file), exist_ok=True)
            
            with open(status_file, 'w') as f:
                json.dump({"processed": processed, "timestamp": time.time()}, f)
            print(f"✅ Đã lưu trạng thái xử lý PDF: {processed}")
            return True
        except Exception as e:
            print(f"❌ Không thể lưu trạng thái xử lý PDF: {e}")
            return False
    
    def load_pdf(self, file_path):
        """
        Tải dữ liệu từ file PDF
        
        Args:
            file_path: Đường dẫn đến file PDF
            
        Returns:
            list: Danh sách các tài liệu
        """
        try:
            loader = PDFPlumberLoader(file_path)
            documents = loader.load()
            print(f"✅ Đã tải file PDF {os.path.basename(file_path)}: {len(documents)} trang")
            return documents
        except Exception as e:
            print(f"❌ Lỗi khi tải file PDF {file_path}: {e}")
            return []
    
    def create_chunks(self, documents, chunk_size=1000, chunk_overlap=200):
        """
        Chia tài liệu thành các đoạn nhỏ hơn
        
        Args:
            documents: Danh sách các tài liệu
            chunk_size: Kích thước mỗi đoạn
            chunk_overlap: Số ký tự chồng lấp giữa các đoạn
            
        Returns:
            list: Danh sách các đoạn văn bản
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True
        )
        text_chunks = text_splitter.split_documents(documents)
        print(f"✅ Đã tạo {len(text_chunks)} đoạn văn bản")
        return text_chunks
    
    def add_metadata_to_chunks(self, chunks, file_path):
        """
        Thêm metadata vào các đoạn văn bản
        
        Args:
            chunks: Danh sách các đoạn văn bản
            file_path: Đường dẫn đến file PDF
            
        Returns:
            list: Danh sách các đoạn văn bản với metadata
        """
        filename = os.path.basename(file_path)
        category = self._detect_category(filename)
        
        # Thêm thông tin vào metadata của mỗi đoạn
        for chunk in chunks:
            chunk.metadata["source"] = filename
            chunk.metadata["file_path"] = file_path
            chunk.metadata["category"] = category
        
        return chunks
    
    def _detect_category(self, filename: str) -> str:
        """
        Phát hiện danh mục từ tên file
        
        Args:
            filename: Tên file
            
        Returns:
            str: Danh mục
        """
        filename_lower = filename.lower()
        
        if any(kw in filename_lower for kw in ["lo_au", "lo-au", "anxiety", "stress", "cang_thang"]):
            return "anxiety"
        elif any(kw in filename_lower for kw in ["tram_cam", "depression", "buon", "tuyetvong"]):
            return "depression"
        elif any(kw in filename_lower for kw in ["cbt", "nhan_thuc", "hanh_vi", "cognitive"]):
            return "cbt_techniques" 
        elif any(kw in filename_lower for kw in ["mindfulness", "thien", "meditation", "chanh_niem"]):
            return "mindfulness"
        elif any(kw in filename_lower for kw in ["khung_hoang", "crisis", "tu_tu", "tu_hai"]):
            return "crisis"
        else:
            return "general_mental_health"
    
    def process_all_pdfs(self):
        """
        Xử lý tất cả các file PDF trong thư mục và tạo vector database
        
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            # Kiểm tra xem đã xử lý chưa
            if PDFProcessor.check_processing_status():
                print("✅ Các file PDF đã được xử lý trước đó. Bỏ qua bước xử lý.")
                return True
                
            # Tìm tất cả các file PDF
            pdf_files = glob.glob(os.path.join(self.pdf_directory, "*.pdf"))
            
            if not pdf_files:
                print(f"❌ Không tìm thấy file PDF nào trong {self.pdf_directory}")
                return False
            
            print(f"🔍 Tìm thấy {len(pdf_files)} file PDF để xử lý")
            
            # Lưu trữ tất cả các đoạn văn bản
            all_chunks = []
            
            # Xử lý từng file PDF
            for pdf_file in pdf_files:
                print(f"⏳ Đang xử lý file: {os.path.basename(pdf_file)}")
                
                # Tải PDF
                documents = self.load_pdf(pdf_file)
                
                if not documents:
                    print(f"⚠️ Không thể tải {pdf_file}, bỏ qua file này")
                    continue
                
                # Chia nhỏ tài liệu
                chunks = self.create_chunks(documents)
                
                if not chunks:
                    print(f"⚠️ Không có đoạn văn bản nào từ {pdf_file}, bỏ qua file này")
                    continue
                
                # Thêm metadata
                chunks_with_metadata = self.add_metadata_to_chunks(chunks, pdf_file)
                
                # Thêm vào danh sách chung
                all_chunks.extend(chunks_with_metadata)
            
            if not all_chunks:
                print("❌ Không có đoạn văn bản nào để xử lý sau khi đọc tất cả các file PDF")
                return False
            
            # Tạo vector database với FAISS
            print(f"⏳ Đang tạo FAISS vector database với {len(all_chunks)} đoạn văn bản...")
            db = FAISS.from_documents(all_chunks, self.embedding_model)
            
            # Lưu vector database
            faiss_path = os.path.join(self.vector_db_path, "db_faiss")
            db.save_local(faiss_path)
            print(f"✅ Đã lưu FAISS vector database vào {faiss_path}")
            
            # Lưu trạng thái đã xử lý
            PDFProcessor.save_processing_status(True)
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi xử lý PDF: {e}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def load_vector_store():
        """
        Tải vector store từ đĩa
        
        Returns:
            FAISS: FAISS vector store hoặc None nếu lỗi
        """
        try:
            faiss_path = os.path.join(Config.VECTOR_DB_PATH, "db_faiss")
            if not os.path.exists(faiss_path):
                print(f"❌ Không tìm thấy FAISS vector database tại {faiss_path}")
                return None
            
            # Tải FAISS với allow_dangerous_deserialization=True
            embedding_model = MISOULEmbeddings()
            db = FAISS.load_local(faiss_path, embedding_model, allow_dangerous_deserialization=True)
            print(f"✅ Đã tải FAISS vector database từ {faiss_path}")
            
            return db
        except Exception as e:
            print(f"❌ Lỗi khi tải FAISS vector database: {e}")
            traceback.print_exc()
            return None

# Hàm main để chạy trực tiếp
if __name__ == "__main__":
    processor = PDFProcessor()
    success = processor.process_all_pdfs()
    if success:
        print("✅ Đã xử lý thành công tất cả các file PDF")
    else:
        print("❌ Có lỗi khi xử lý các file PDF")