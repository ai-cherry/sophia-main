"""
Sophia AI - Vector Database Integration
Comprehensive integration with Pinecone and Weaviate for semantic search and AI-powered insights
"""

import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import pinecone
import weaviate
from sentence_transformers import SentenceTransformer

@dataclass
class VectorConfig:
    """Configuration for vector database operations"""
    pinecone_api_key: str
    pinecone_environment: str = "us-west1-gcp"
    pinecone_index_name: str = "sophia-payready"
    weaviate_url: str = ""
    weaviate_api_key: str = ""
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_dimension: int = 1536
    batch_size: int = 100
    similarity_threshold: float = 0.7

class VectorIntegration:
    """
    Advanced vector database integration for Sophia AI Pay Ready platform.
    Provides semantic search, embedding generation, and AI-powered insights.
    """
    
    def __init__(self, config: VectorConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(config.embedding_model)
        
        # Initialize vector databases
        self.setup_pinecone()
        self.setup_weaviate()
        
        # Performance tracking
        self.query_stats = {
            'total_queries': 0,
            'avg_response_time': 0.0,
            'cache_hits': 0
        }
    
    def setup_logging(self):
        """Setup logging for vector operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def setup_pinecone(self):
        """Initialize Pinecone connection and index"""
        try:
            pinecone.init(
                api_key=self.config.pinecone_api_key,
                environment=self.config.pinecone_environment
            )
            
            # Create index if it doesn't exist
            if self.config.pinecone_index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self.config.pinecone_index_name,
                    dimension=self.config.vector_dimension,
                    metric="cosine"
                )
                self.logger.info(f"Created Pinecone index: {self.config.pinecone_index_name}")
            
            self.pinecone_index = pinecone.Index(self.config.pinecone_index_name)
            self.logger.info("Pinecone connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Pinecone: {str(e)}")
            self.pinecone_index = None
    
    def setup_weaviate(self):
        """Initialize Weaviate connection and schema"""
        try:
            self.weaviate_client = weaviate.Client(
                url=self.config.weaviate_url,
                auth_client_secret=weaviate.AuthApiKey(api_key=self.config.weaviate_api_key)
            )
            
            # Create schema if it doesn't exist
            self.create_weaviate_schema()
            self.logger.info("Weaviate connection established")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Weaviate: {str(e)}")
            self.weaviate_client = None
    
    def create_weaviate_schema(self):
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
            # Check if schema exists
            existing_schema = self.weaviate_client.schema.get()
            class_names = [cls["class"] for cls in existing_schema.get("classes", [])]
            
            if "SophiaPayReady" not in class_names:
                self.weaviate_client.schema.create(schema)
                self.logger.info("Created Weaviate schema for SophiaPayReady")
            
        except Exception as e:
            self.logger.warning(f"Schema creation warning: {str(e)}")
    
    def generate_embeddings(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings using SentenceTransformers"""
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
    
    def index_content_pinecone(self, content_id: str, text: str, metadata: Dict[str, Any]) -> bool:
        """Index content in Pinecone"""
        if not self.pinecone_index:
            return False
        
        try:
            # Generate embedding
            embedding = self.generate_embeddings(text)
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
    
    def index_content_weaviate(self, content_id: str, text: str, metadata: Dict[str, Any]) -> bool:
        """Index content in Weaviate"""
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
    
    def index_content(self, content_id: str, text: str, metadata: Dict[str, Any]) -> Dict[str, bool]:
        """Index content in both vector databases"""
        results = {
            "pinecone": self.index_content_pinecone(content_id, text, metadata),
            "weaviate": self.index_content_weaviate(content_id, text, metadata)
        }
        
        return results
    
    def batch_index_content(self, content_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Batch index multiple content items"""
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
                
                index_results = self.index_content(content_id, text, metadata)
                
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
    
    def search_pinecone(self, query: str, top_k: int = 10, filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """Search content in Pinecone"""
        if not self.pinecone_index:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings(query)
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
    
    def search_weaviate(self, query: str, top_k: int = 10, category_filter: Optional[str] = None) -> List[Dict]:
        """Search content in Weaviate"""
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
    
    def hybrid_search(self, query: str, top_k: int = 10, category_filter: Optional[str] = None) -> List[Dict]:
        """Perform hybrid search across both vector databases"""
        start_time = datetime.now()
        
        # Search both databases
        pinecone_results = self.search_pinecone(query, top_k)
        weaviate_results = self.search_weaviate(query, top_k, category_filter)
        
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
    
    def semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        try:
            embeddings = self.generate_embeddings([text1, text2])
            if len(embeddings) != 2:
                return 0.0
            
            # Calculate cosine similarity
            vec1 = np.array(embeddings[0])
            vec2 = np.array(embeddings[1])
            
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Similarity calculation failed: {str(e)}")
            return 0.0
    
    def get_related_content(self, content_id: str, top_k: int = 5) -> List[Dict]:
        """Find content related to a specific item"""
        # This would typically involve getting the content by ID first,
        # then searching for similar content
        # Simplified implementation for demo
        return []
    
    def delete_content(self, content_id: str) -> Dict[str, bool]:
        """Delete content from both vector databases"""
        results = {"pinecone": False, "weaviate": False}
        
        # Delete from Pinecone
        if self.pinecone_index:
            try:
                self.pinecone_index.delete(ids=[content_id])
                results["pinecone"] = True
                self.logger.info(f"Deleted {content_id} from Pinecone")
            except Exception as e:
                self.logger.error(f"Failed to delete {content_id} from Pinecone: {str(e)}")
        
        # Delete from Weaviate
        if self.weaviate_client:
            try:
                self.weaviate_client.data_object.delete(
                    uuid=content_id,
                    class_name="SophiaPayReady"
                )
                results["weaviate"] = True
                self.logger.info(f"Deleted {content_id} from Weaviate")
            except Exception as e:
                self.logger.error(f"Failed to delete {content_id} from Weaviate: {str(e)}")
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = self.query_stats.copy()
        
        # Add database health checks
        stats["pinecone_healthy"] = self.pinecone_index is not None
        stats["weaviate_healthy"] = self.weaviate_client is not None
        
        if self.pinecone_index:
            try:
                index_stats = self.pinecone_index.describe_index_stats()
                stats["pinecone_vector_count"] = index_stats.total_vector_count
            except Exception:
                stats["pinecone_vector_count"] = "unknown"
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on vector databases"""
        health = {
            "overall_healthy": True,
            "pinecone": {"healthy": False, "error": None},
            "weaviate": {"healthy": False, "error": None}
        }
        
        # Check Pinecone
        if self.pinecone_index:
            try:
                self.pinecone_index.describe_index_stats()
                health["pinecone"]["healthy"] = True
            except Exception as e:
                health["pinecone"]["error"] = str(e)
                health["overall_healthy"] = False
        else:
            health["pinecone"]["error"] = "Not initialized"
            health["overall_healthy"] = False
        
        # Check Weaviate
        if self.weaviate_client:
            try:
                self.weaviate_client.schema.get()
                health["weaviate"]["healthy"] = True
            except Exception as e:
                health["weaviate"]["error"] = str(e)
                health["overall_healthy"] = False
        else:
            health["weaviate"]["error"] = "Not initialized"
            health["overall_healthy"] = False
        
        return health


# Example usage and configuration
if __name__ == "__main__":
    # Configuration
    config = VectorConfig(
        pinecone_api_key="pcsk_7PHV2G_Mj1rRCwiHZ7YsuuzJcqKch9akzNKXv6mfwDX65DenD8Q72w3Qjh4AmuataTnEDW",
        weaviate_url="https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud",
        weaviate_api_key="VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf"
    )
    
    # Initialize vector integration
    vector_integration = VectorIntegration(config)
    
    # Example content for testing
    test_content = [
        {
            "id": "revenue_q4_2024",
            "text": "Q4 2024 revenue reached $1.2M, representing 45% growth year-over-year. Key drivers included enterprise client acquisitions and product expansion.",
            "metadata": {
                "title": "Q4 2024 Revenue Report",
                "category": "revenue",
                "source": "financial_reports",
                "timestamp": "2024-12-31T23:59:59Z"
            }
        },
        {
            "id": "customer_satisfaction_2024",
            "text": "Customer satisfaction scores improved to 4.8/5 in 2024, with 92% of customers rating our support as excellent.",
            "metadata": {
                "title": "Customer Satisfaction Survey Results",
                "category": "customers",
                "source": "surveys",
                "timestamp": "2024-12-15T10:00:00Z"
            }
        }
    ]
    
    # Test operations
    try:
        # Health check
        health = vector_integration.health_check()
        print("Health check:", health)
        
        # Index test content
        batch_results = vector_integration.batch_index_content(test_content)
        print("Batch indexing results:", batch_results)
        
        # Test search
        search_results = vector_integration.hybrid_search("revenue growth", top_k=5)
        print(f"Search results: {len(search_results)} items found")
        
        # Performance stats
        stats = vector_integration.get_performance_stats()
        print("Performance stats:", stats)
        
    except Exception as e:
        print(f"Vector integration test failed: {e}")

