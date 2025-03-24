# app/qdrant_manager.py
import pickle
import os
import numpy as np
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
import uuid
import json
import traceback

class SimpleDocument:
    """Lớp Document tương thích với API của LangChain"""
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

class QdrantManager:
    """Quản lý Vector Database Qdrant"""
    
    def __init__(self, collection_name="misoul_docs"):
        """Khởi tạo kết nối đến Qdrant và tạo collection nếu chưa tồn tại"""
        self.client = QdrantClient(":memory:")  # Lưu trữ trong bộ nhớ
        self.collection_name = collection_name
        
        # Tạo collection mới
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=768,  # Kích thước mặc định, có thể điều chỉnh
                    distance=models.Distance.COSINE
                )
            )
            print(f"Đã tạo collection mới: {collection_name}")
        except Exception as e:
            print(f"Collection đã tồn tại hoặc lỗi: {e}")
    
    def import_from_embedding_model(self, embedding_model_path):
        """Import dữ liệu từ embedding model và tạo dữ liệu mẫu"""
        try:
            # Tải embedding model
            with open(embedding_model_path, "rb") as f:
                embedding_model = pickle.load(f)
                print(f"Đã tải embedding model từ {embedding_model_path}")
            
            # Tạo dữ liệu mẫu
            anxiety_docs = [
                "Lo âu là phản ứng tự nhiên của cơ thể đối với stress. Đó là cảm giác sợ hãi hoặc lo lắng về những gì sắp xảy ra.",
                "Các triệu chứng lo âu bao gồm: tim đập nhanh, khó thở, lo lắng quá mức, khó tập trung, mất ngủ và căng thẳng.",
                "Kỹ thuật thở sâu có thể giúp giảm lo âu: hít vào trong 4 giây, giữ trong 7 giây, và thở ra trong 8 giây.",
                "Tập thể dục đều đặn giúp giảm lo âu bằng cách giải phóng endorphin và cải thiện tâm trạng.",
                "Thiền và mindfulness là các kỹ thuật hiệu quả để kiểm soát lo âu dài hạn."
            ]

            depression_docs = [
                "Trầm cảm là rối loạn tâm trạng gây ra cảm giác buồn bã và mất hứng thú kéo dài, ảnh hưởng đến khả năng hoạt động hàng ngày.",
                "Các triệu chứng trầm cảm bao gồm: buồn bã kéo dài, mất hứng thú, mệt mỏi, khó tập trung, thay đổi cảm giác đói và giấc ngủ.",
                "Liệu pháp nhận thức hành vi (CBT) giúp nhận diện và thay đổi các mẫu suy nghĩ tiêu cực liên quan đến trầm cảm.",
                "Kết nối xã hội và chia sẻ cảm xúc với người khác có thể giúp giảm cảm giác cô đơn và cải thiện tâm trạng.",
                "Thiết lập mục tiêu nhỏ và đạt được chúng là cách hiệu quả để xây dựng lại cảm giác thành công và giá trị bản thân."
            ]

            cbt_docs = [
                "Liệu pháp Nhận thức Hành vi (CBT) tập trung vào nhận diện và thay đổi các mẫu suy nghĩ và hành vi tiêu cực.",
                "Kỹ thuật ABC trong CBT: A (Sự kiện kích hoạt), B (Niềm tin/suy nghĩ), C (Hậu quả cảm xúc) giúp hiểu mối liên hệ giữa suy nghĩ và cảm xúc.",
                "Nhật ký suy nghĩ là công cụ CBT giúp ghi lại và thách thức các suy nghĩ tiêu cực tự động.",
                "Kỹ thuật khởi tạo hành vi là phương pháp CBT giúp tăng cường các hoạt động tích cực để cải thiện tâm trạng.",
                "Kỹ thuật giải quyết vấn đề trong CBT gồm: xác định vấn đề, liệt kê giải pháp, đánh giá và chọn giải pháp tốt nhất, thực hiện, đánh giá kết quả."
            ]

            mindfulness_docs = [
                "Mindfulness là việc chú ý có ý thức vào thời điểm hiện tại, không phán xét các suy nghĩ và cảm xúc đang diễn ra.",
                "Meditation hơi thở cơ bản: tập trung vào hơi thở, khi tâm trí lang thang, nhẹ nhàng đưa sự chú ý trở lại hơi thở.",
                "Body scan là kỹ thuật mindfulness giúp nâng cao nhận thức về cơ thể bằng cách di chuyển sự chú ý từng phần của cơ thể.",
                "Eating meditation là thực hành mindfulness khi ăn, chú ý đến mùi vị, kết cấu và cảm giác khi ăn thức ăn.",
                "Walking meditation là thực hành chú ý đến từng bước chân, cảm giác của chân tiếp xúc với mặt đất khi đi bộ."
            ]

            crisis_docs = [
                "Trong trường hợp khủng hoảng tâm lý nghiêm trọng, điều quan trọng là tìm kiếm sự giúp đỡ chuyên nghiệp ngay lập tức.",
                "Tổng đài tư vấn tâm lý miễn phí 1800-8440 hoạt động 24/7 để hỗ trợ trong trường hợp khủng hoảng.",
                "Khi có ý nghĩ tự hại, hãy ở bên cạnh người thân hoặc bạn bè, không nên ở một mình.",
                "Kỹ thuật grounding 5-4-3-2-1: xác định 5 thứ bạn thấy, 4 thứ bạn chạm, 3 thứ bạn nghe, 2 thứ bạn ngửi, 1 thứ bạn nếm.",
                "Trong trường hợp khẩn cấp, hãy gọi cứu thương (115) hoặc đến phòng cấp cứu gần nhất."
            ]
            
            # Tạo danh sách tài liệu và metadata
            docs = []
            metadata_list = []
            
            # Thêm dữ liệu từ từng danh mục
            for doc in anxiety_docs:
                docs.append(doc)
                metadata_list.append({"category": "anxiety"})
                
            for doc in depression_docs:
                docs.append(doc)
                metadata_list.append({"category": "depression"})
                
            for doc in cbt_docs:
                docs.append(doc)
                metadata_list.append({"category": "cbt_techniques"})
                
            for doc in mindfulness_docs:
                docs.append(doc)
                metadata_list.append({"category": "mindfulness"})
                
            for doc in crisis_docs:
                docs.append(doc)
                metadata_list.append({"category": "crisis"})
            
            # Tạo embeddings nếu có thể
            embeddings = []
            try:
                if hasattr(embedding_model, 'embed_documents'):
                    embeddings = embedding_model.embed_documents(docs)
                    print(f"Đã tạo {len(embeddings)} embeddings từ model")
                else:
                    # Tạo embeddings ngẫu nhiên
                    embeddings = [self._create_simple_embedding(doc) for doc in docs]
            except Exception as e:
                print(f"Lỗi khi tạo embeddings: {e}")
                # Fallback to simple embeddings
                embeddings = [self._create_simple_embedding(doc) for doc in docs]
            
            # Thêm tài liệu vào Qdrant
            self.add_documents_with_embeddings(docs, embeddings, metadata_list)
            
            return len(docs)
            
        except Exception as e:
            print(f"Lỗi khi import từ embedding model: {e}")
            traceback.print_exc()
            return 0
    
    def add_documents_with_embeddings(self, documents, embeddings, metadata_list=None):
        """Thêm tài liệu và embeddings vào Qdrant"""
        if metadata_list is None:
            metadata_list = [{} for _ in documents]
        
        # Chuẩn bị points để upsert
        points = []
        for i, (doc, embedding, metadata) in enumerate(zip(documents, embeddings, metadata_list)):
            # Thêm text vào metadata
            metadata["text"] = doc
            
            # Tạo point
            points.append(models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload=metadata
            ))
        
        # Upsert points vào collection
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        print(f"Đã thêm {len(points)} tài liệu vào Qdrant")
        return self
    
    def add_documents(self, documents, metadata=None):
        """Thêm tài liệu vào Qdrant"""
        if metadata is None:
            metadata = [{} for _ in documents]
            
        # Tạo embeddings
        embeddings = [self._create_simple_embedding(doc) for doc in documents]
        
        # Thêm tài liệu với embeddings
        return self.add_documents_with_embeddings(documents, embeddings, metadata)
    
    def similarity_search(self, query, k=3):
        """Tìm kiếm các tài liệu tương tự với query"""
        # Tạo embedding từ query
        query_embedding = self._create_simple_embedding(query)
        
        # Tìm kiếm
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=k
        )
        
        # Chuyển đổi kết quả thành đối tượng Document
        documents = []
        for result in search_result:
            metadata = dict(result.payload)
            text = metadata.pop("text", "")
            doc = SimpleDocument(page_content=text, metadata=metadata)
            documents.append(doc)
        
        return documents
    
    def _create_simple_embedding(self, text):
        """Tạo embedding đơn giản từ text"""
        if isinstance(text, str):
            # Hàm này tạo vector ngẫu nhiên nhưng nhất quán cho cùng một chuỗi
            np.random.seed(hash(text) % 2**32)
            return np.random.rand(768).tolist()
        else:
            # Nếu không phải string, có thể là embedding
            return text