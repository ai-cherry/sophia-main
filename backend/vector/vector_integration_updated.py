"""
Sophia AI - Vector Database Integration (Updated)
Comprehensive integration with Pinecone and Weaviate for semantic search and AI-powered insights
Using centralized configuration management
"""

import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import os
import hashlib
import openai
import pinecone
import weaviate
from sentence_transformers import SentenceTransformer

from ..core.config_manager import get_config, get_secret, get_api_client

class VectorIntegration:
    """
    Advanced vector database integration for Sophia AI Pay Ready platform.
    Provides semantic search, embedding generation, and AI-powered insights.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # Initialize with default values
        self.pinecone_api_key = None
        self.pinecone_environment = "us-west1-gcp"
        self.pinecone_index_name = "sophia-payready"
        self.weaviate_url = ""
        self.weaviate_api_key = ""
        self.embedding_model_name = "all-MiniLM-L6-v2"
        self.vector_dimension = 1536
        self.batch_size = 100
        self.similarity_threshold = 0.7
        
        # Initialize components
        self.embedding_model = None
        self.pinecone_index = None
        self.weaviate_client = None
        
        # Performance tracking
        self.query_stats = {
            'total_queries': 0,
            'avg_response_time': 0.0,
            'cache_hits': 0
        }
        
        # Initialization flag
        self.initialized = False
    
    def setup_logging(self):
        """Setup logging for vector operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def initialize(self):
        """Initialize the vector integration with configuration from centralized manager"""
        if self.initialized:
            return
        
        try:
            # Get Pinecone configuration
            pinecone_config = await get_config("pinecone")
            if pinecone_config:
                self.pinecone_api_key = pinecone_config.secrets.get("api_key")
                self.pinecone_environment = pinecone_config.config.get("environment", self.pinecone_environment)
                self.pinecone_index_name = pinecone_config.config.get("index_name", self.pinecone_index_name)
            
            # Get Weaviate configuration
            weaviate_config = await get_config("weaviate")
            if weaviate_config:
                self.weaviate_url = weaviate_config.config.get("url", self.weaviate_url)
                self.weaviate_api_key = weaviate_config.secrets.get("api_key", self.weaviate_api_key)
            
            # Get vector configuration
            vector_config = await get_config("vector")
            if vector_config:
                self.embedding_model_name = vector_config.config.get("embedding_model", self.embedding_model_name)
                self.vector_dimension = vector_config.config.get("vector_dimension", self.vector_dimension)
                self.batch_size = vector_config.config.get("batch_size", self.batch_size)
                self.similarity_threshold = vector_config.config.get("similarity_threshold", self.similarity_threshold)
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            
            # Initialize vector databases
            await self.setup_pinecone()
            await self.setup_weaviate()
            
            self.initialized = True
            self.logger.info("Vector integration initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize vector integration: {e}")
            raise
    
    async def setup_pinecone(self):
        """Initialize Pinecone connection and index"""
        try:
            if not self.pinecone_api_key:
                self.logger.warning("Pinecone API key not found, skipping Pinecone initialization")
                return
            
            pinecone.init(
                api_key=self.pinecone_api_key,
                environment=self.pinecone_environment
            )
            
            # Create index if it doesn't exist
            if self.pinecone_index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self.pinecone_index_name,
                    dimension=self.vector_dimension,
                    metric="cosine"
                )
                self.logger.info(f"Created Pinecone index: {self.pinecone_index_name}")
            
            self.pinecone_index = pinecone.Index(self.pinecone_index_name)
            self.logger.info("Pinecone connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Pinecone: {str(e)}")
            self.pinecone_index = None
    
    async def setup_weaviate(self):
        """Initialize Weaviate connection and schema"""
        try:
            if not self.weaviate_url or not self.weaviate_api_key:
                self.logger.warning("Weaviate URL or API key not found, skipping Weaviate initialization")
                return
            
            self.weaviate_client = weaviate.Client(
                url=self.weaviate_url,
                auth_client_secret=weaviate.AuthApiKey(api_key=self.weaviate_api_key)
            )
            
            # Create schema if it doesn't exist
            await self.create_weaviate_schema()
            self.logger.info("Weaviate connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Weaviate: {str(e)}")
            self.weaviate_client = None
    
    async def create_weaviate_schema(self):
        """Create Weaviate schema for Sophia AI business intelligence"""
        schema = {
            "classes": [
                {
                    "class": "SophiaPayReady",
                    "description": "Business intelligence content for Pay Ready company",
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Main content text"
                        },
                        {
                            "name": "title",
                            "dataType": ["string"],
                            "description": "Content title"
                        },
                        {
                            "name": "category",
                            "dataType": ["string"],
                            "description": "Content category (revenue, customers, operations, etc.)"
                        },
                        {
                            "name": "source",
                            "dataType": ["string"],
                            "description": "Data source (slack, gong, database, etc.)"
                        },
                        {
                            "name": "timestamp",
                            "dataType": ["date"],
                            "description": "Content creation timestamp"
                        },
                        {
                            "name": "metadata",
                            "dataType": ["object"],
                            "description": "Additional metadata"
                        }
                    ],
                    "vectorizer": "text2vec-openai",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "model": "ada",
                            "modelVersion": "002",
                            "type": "text"
                        }
                    }
                }
            ]
        }
        
        try:
            if not self.weaviate_client:
                return
                
            # Check if schema exists
            existing_schema = self.weaviate_client.schema.get()
            class_names = [cls["class"] for cls in existing_schema.get("classes", [])]
            
            if "SophiaPayReady" not in class_names:
                self.weaviate_client.schema.create(schema)
                self.logger.info("Created Weaviate schema for SophiaPayReady")
            
        except Exception as e:
            self.logger.warning(f"Schema creation warning: {str(e)}")
    
    async def generate_embeddings(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings using SentenceTransformers"""
        if not self.initialized:
            await self.initialize()
            
        try:
            if isinstance(texts, str):
                embeddings = self.embedding_model.encode([texts])
                return embeddings[0].tolist()
            else:
                embeddings = self.embedding_model.encode(texts)
                return [emb.tolist() for emb in embeddings]
                
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {str(e)}")
            return [] if isinstance(texts, list) else []
    
    async def index_content_pinecone(self, content_id: str, text: str, metadata: Dict[str, Any]) -> bool:
        """Index content in Pinecone"""
        if not self.initialized:
            await self.initialize()
            
        if not self.pinecone_index:
            return False
        
        try:
            # Generate embedding
            embedding = await self.generate_embeddings(text)
            if not embedding:
                return False
            
            # Prepare metadata (Pinecone has metadata size limits)
            safe_metadata = {
                "title": metadata.get("title", "")[:100],
                "category": metadata.get("category", "")[:50],
                "source": metadata.get("source", "")[:50],
                "timestamp": metadata.get("timestamp", datetime.now().isoformat())
            }
            
            # Upsert to Pinecone
            self.pinecone_index.upsert(
                vectors=[(content_id, embedding, safe_metadata)]
            )
            
            self.logger.info(f"Indexed content {content_id} in Pinecone")
            return True
            
        except Exception as e:
            self.logger.error(f"Pinecone indexing failed for {content_id}: {str(e)}")
            return False
    
    async def index_content_weaviate(self, content_id: str, text: str, metadata: Dict[str, Any]) -> bool:
        """Index content in Weaviate"""
        if not self.initialized:
            await self.initialize()
            
        if not self.weaviate_client:
            return False
        
        try:
            data_object = {
                "content": text,
                "title": metadata.get("title", ""),
                "category": metadata.get("category", ""),
                "source": metadata.get("source", ""),
                "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                "metadata": metadata
            }
            
            # Add to Weaviate
            self.weaviate_client.data_object.create(
                data_object=data_object,
                class_name="SophiaPayReady",
                uuid=content_id
            )
            
            self.logger.info(f"Indexed content {content_id} in Weaviate")
            return True
            
        except Exception as e:
            self.logger.error(f"Weaviate indexing failed for {content_id}: {str(e)}")
            return False
    
    async def index_content(self, content_id: str, text: str, metadata: Dict[str, Any]) -> Dict[str, bool]:
        """Index content in both vector databases"""
        if not self.initialized:
            await self.initialize()
            
        results = {
            "pinecone": await self.index_content_pinecone(content_id, text, metadata),
            "weaviate": await self.index_content_weaviate(content_id, text, metadata)
        }
        
        return results
    
    async def batch_index_content(self, content_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Batch index multiple content items"""
        if not self.initialized:
            await self.initialize()
            
        results = {
            "total": len(content_batch),
            "successful": 0,
            "failed": 0,
            "pinecone_success": 0,
            "weaviate_success": 0,
            "errors": []
        }
        
        for item in content_batch:
            try:
                content_id = item["id"]
                text = item["text"]
                metadata = item.get("metadata", {})
                
                index_results = await self.index_content(content_id, text, metadata)
                
                if index_results["pinecone"]:
                    results["pinecone_success"] += 1
                if index_results["weaviate"]:
                    results["weaviate_success"] += 1
                
                if any(index_results.values()):
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Item {item.get('id', 'unknown')}: {str(e)}")
        
        self.logger.info(f"Batch indexing completed: {results['successful']}/{results['total']} successful")
        return results
    
    async def search_pinecone(self, query: str, top_k: int = 10, filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """Search content in Pinecone"""
        if not self.initialized:
            await self.initialize()
            
        if not self.pinecone_index:
            return []
        
        try:
            # Generate query embedding
            query_embedding = await self.generate_embeddings(query)
            if not query_embedding:
                return []
            
            # Search Pinecone
            search_results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_metadata,
                include_metadata=True
            )
            
            # Format results
            results = []
            for match in search_results.matches:
                results.append({
                    "id": match.id,
                    "score": float(match.score),
                    "metadata": match.metadata,
                    "source": "pinecone"
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Pinecone search failed: {str(e)}")
            return []
    
    async def search_weaviate(self, query: str, top_k: int = 10, category_filter: Optional[str] = None) -> List[Dict]:
        """Search content in Weaviate"""
        if not self.initialized:
            await self.initialize()
            
        if not self.weaviate_client:
            return []
        
        try:
            # Build query
            where_filter = None
            if category_filter:
                where_filter = {
                    "path": ["category"],
                    "operator": "Equal",
                    "valueString": category_filter
                }
            
            # Search Weaviate
            search_results = (
                self.weaviate_client.query
                .get("SophiaPayReady", ["content", "title", "category", "source", "timestamp", "metadata"])
                .with_near_text({"concepts": [query]})
                .with_limit(top_k)
                .with_additional(["certainty"])
            )
            
            if where_filter:
                search_results = search_results.with_where(where_filter)
            
            results_data = search_results.do()
            
            # Format results
            results = []
            if "data" in results_data and "Get" in results_data["data"]:
                for item in results_data["data"]["Get"]["SophiaPayReady"]:
                    results.append({
                        "content": item.get("content", ""),
                        "title": item.get("title", ""),
                        "category": item.get("category", ""),
                        "timestamp": item.get("timestamp", ""),
                        "metadata": item.get("metadata", {}),
                        "score": item.get("_additional", {}).get("certainty", 0.0),
                        "source": "weaviate"
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Weaviate search failed: {str(e)}")
            return []
    
    async def hybrid_search(self, query: str, top_k: int = 10, category_filter: Optional[str] = None) -> List[Dict]:
        """Perform hybrid search across both vector databases"""
        if not self.initialized:
            await self.initialize()
            
        start_time = datetime.now()
        
        # Search both databases
        pinecone_results = await self.search_pinecone(query, top_k)
        weaviate_results = await self.search_weaviate(query, top_k, category_filter)
        
        # Merge and deduplicate results
        all_results = pinecone_results + weaviate_results
        
        # Sort by relevance score (descending)
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Remove duplicates and limit results
        seen_ids = set()
        unique_results = []
        
        for result in all_results:
            result_id = result.get("id") or result.get("title", "")
            if result_id not in seen_ids and len(unique_results) < top_k:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        # Update performance stats
        response_time = (datetime.now() - start_time).total_seconds()
        self.query_stats['total_queries'] += 1
        self.query_stats['avg_response_time'] = (
            (self.query_stats['avg_response_time'] * (self.query_stats['total_queries'] - 1) + response_time) /
            self.query_stats['total_queries']
        )
        
        self.logger.info(f"Hybrid search completed in {response_time:.3f}s, returned {len(unique_results)} results")
        return unique_results
    
    async def semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        if not self.initialized:
            await self.initialize()
            
        try:
            embeddings = await self.generate_embeddings([text1, text2])
            if len(embeddings) != 2:
                return 0.0
            
            # Calculate cosine similarity
            vec1 = np.array(embeddings[0])
            vec2 = np.array(embeddings[1])
            
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            return float(similarity)
        except Exception as e:
            self.logger.error(f"Semantic similarity calculation failed: {str(e)}")
            return 0.0

# Create singleton instance
vector_integration = VectorIntegration()

