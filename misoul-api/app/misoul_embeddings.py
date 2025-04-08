# app/misoul_embeddings.py
from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class MISOULEmbeddings:
    """
    Lớp embeddings tương thích với LangChain
    
    Sử dụng TF-IDF thay vì CountVectorizer để có hiệu quả tốt hơn
    """
    
    def __init__(self, max_features=5000):
        """
        Khởi tạo embedding model
        
        Args:
            max_features: Số lượng tính năng tối đa
        """
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
            return np.zeros(self.vectorizer.max_features).tolist()
        
        embedding = self.vectorizer.transform([text]).toarray()[0]
        return embedding.tolist()