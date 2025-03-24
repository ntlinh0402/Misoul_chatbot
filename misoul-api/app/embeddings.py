# app/embeddings.py
from typing import List
from sklearn.feature_extraction.text import CountVectorizer

class SimpleEmbeddings:
    def __init__(self, max_features=5000):
        self.vectorizer = CountVectorizer(max_features=max_features)
        self.fitted = False
        
    def fit(self, texts):
        self.vectorizer.fit(texts)
        self.fitted = True
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.fitted:
            self.fit(texts)
        embeddings = self.vectorizer.transform(texts).toarray()
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        if not self.fitted:
            raise ValueError("Model not fitted yet")
        embedding = self.vectorizer.transform([text]).toarray()[0]
        return embedding.tolist()