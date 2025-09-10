from pinecone import Pinecone, ServerlessSpec
from app.config import settings
import numpy as np
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PineconeService:
    def __init__(self):
        if not settings.pinecone_api_key:
            logger.warning("Pinecone API key not provided. Vector operations will be disabled.")
            self.pc = None
            self.index_name = settings.pinecone_index_name
            self.dimension = 1536
            return
        
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.dimension = 1536  # OpenAI embedding dimension
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        if not self.pc:
            return
            
        try:
            if not self.pc.has_index(self.index_name):
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Created Pinecone index: {self.index_name}")
            else:
                logger.info(f"Pinecone index already exists: {self.index_name}")
        except Exception as e:
            logger.error(f"Error ensuring Pinecone index exists: {e}")
            raise
    
    def get_index(self):
        if not self.pc:
            raise Exception("Pinecone not configured")
        return self.pc.Index(self.index_name)
    
    def upsert_vectors(self, vectors: List[Dict[str, Any]], namespace: str = "default"):
        if not self.pc:
            logger.warning("Pinecone not configured, skipping vector upsert")
            return
            
        try:
            index = self.get_index()
            index.upsert(vectors=vectors, namespace=namespace)
            logger.info(f"Upserted {len(vectors)} vectors to Pinecone namespace: {namespace}")
        except Exception as e:
            logger.error(f"Error upserting vectors to Pinecone: {e}")
            raise
    
    def query_vectors(self, query_vector: List[float], top_k: int = 10, filter_dict: Optional[Dict] = None, namespace: str = "default"):
        if not self.pc:
            logger.warning("Pinecone not configured, returning empty results")
            return None
            
        try:
            index = self.get_index()
            results = index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=True,
                namespace=namespace
            )
            return results
        except Exception as e:
            logger.error(f"Error querying vectors from Pinecone: {e}")
            raise
    
    def delete_vectors(self, ids: List[str], namespace: str = "default"):
        if not self.pc:
            logger.warning("Pinecone not configured, skipping vector deletion")
            return
            
        try:
            index = self.get_index()
            index.delete(ids=ids, namespace=namespace)
            logger.info(f"Deleted {len(ids)} vectors from Pinecone namespace: {namespace}")
        except Exception as e:
            logger.error(f"Error deleting vectors from Pinecone: {e}")
            raise
    
    def get_vector_stats(self):
        if not self.pc:
            logger.warning("Pinecone not configured, returning empty stats")
            return None
            
        try:
            index = self.get_index()
            stats = index.describe_index_stats()
            return stats
        except Exception as e:
            logger.error(f"Error getting vector stats from Pinecone: {e}")
            raise

# Global instance
pinecone_service = PineconeService()
