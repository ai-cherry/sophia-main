"""
Sophia AI - Optimized Vector Database Configuration
Production-ready setup for Pinecone and Weaviate with advanced features
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time

# Pinecone Configuration
@dataclass
class PineconeConfig:
    """Optimized Pinecone configuration for Sophia AI business intelligence"""
    
    api_key: str
    environment: str = "us-west-2"
    
    # Index Configuration
    primary_index: str = "sophia-payready"
    secondary_index: str = "sophia-business"
    dimension: int = 1536  # OpenAI embedding standard
    metric: str = "cosine"  # Best for semantic similarity
    
    # Performance Optimization
    batch_size: int = 100  # Optimal for throughput
    upsert_timeout: int = 30
    query_timeout: int = 10
    max_retries: int = 3
    backoff_factor: float = 0.5
    
    # Metadata Configuration
    metadata_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata_config is None:
            self.metadata_config = {
                "indexed": [
                    "category",      # business, finance, operations, strategy
                    "department",    # sales, marketing, finance, hr, operations
                    "priority",      # high, medium, low
                    "date_range",    # quarterly, monthly, weekly, daily
                    "data_source",   # slack, gong, internal_db, api_feed
                    "confidence",    # 0.0 to 1.0
                    "business_unit", # pay_ready_core, pay_ready_plus, enterprise
                    "metric_type"    # revenue, growth, efficiency, satisfaction
                ]
            }

@dataclass
class WeaviateConfig:
    """Optimized Weaviate configuration for Sophia AI"""
    
    url: str
    api_key: str
    grpc_url: str = None
    
    # Class Configuration
    class_name: str = "SophiaPayReady"
    vectorizer: str = "text2vec-openai"
    generative_module: str = "generative-openai"
    
    # Performance Configuration
    batch_size: int = 100
    consistency_level: str = "QUORUM"  # Balance between consistency and performance
    query_timeout: int = 30
    max_connections: int = 50
    
    # Advanced Features
    reranker_module: str = "reranker-cohere"
    multimodal_module: str = "multi2vec-openai"
    
    def __post_init__(self):
        if self.grpc_url is None:
            self.grpc_url = f"grpc-{self.url.split('//')[1]}"

class OptimizedVectorDatabaseManager:
    """
    Advanced vector database management for Sophia AI
    Implements best practices for business intelligence workloads
    """
    
    def __init__(self, pinecone_config: PineconeConfig, weaviate_config: WeaviateConfig):
        self.pinecone_config = pinecone_config
        self.weaviate_config = weaviate_config
        self.logger = logging.getLogger(__name__)
        
        # Initialize connections
        self.setup_pinecone()
        self.setup_weaviate()
        
        # Performance metrics
        self.metrics = {
            "pinecone_queries": 0,
            "weaviate_queries": 0,
            "hybrid_queries": 0,
            "avg_latency": 0.0,
            "error_count": 0
        }
    
    def setup_pinecone(self):
        """Initialize and optimize Pinecone connection"""
        try:
            import pinecone
            
            # Initialize with optimized settings
            pinecone.init(
                api_key=self.pinecone_config.api_key,
                environment=self.pinecone_config.environment
            )
            
            # Verify indexes exist and are optimized
            self.verify_pinecone_indexes()
            
            self.logger.info("Pinecone initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Pinecone: {str(e)}")
            raise
    
    def setup_weaviate(self):
        """Initialize and optimize Weaviate connection"""
        try:
            import weaviate
            
            # Initialize with authentication and optimization
            auth_config = weaviate.AuthApiKey(api_key=self.weaviate_config.api_key)
            
            self.weaviate_client = weaviate.Client(
                url=self.weaviate_config.url,
                auth_client_secret=auth_config,
                timeout_config=(5, 15),  # (connection, read) timeouts
                additional_headers={
                    "X-OpenAI-Api-Key": "your-openai-key",  # For vectorizer
                    "X-Cohere-Api-Key": "your-cohere-key"   # For reranker
                }
            )
            
            # Verify schema and optimize
            self.setup_weaviate_schema()
            
            self.logger.info("Weaviate initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Weaviate: {str(e)}")
            raise
    
    def verify_pinecone_indexes(self):
        """Verify and optimize Pinecone indexes"""
        import pinecone
        
        # Check primary index
        if self.pinecone_config.primary_index not in pinecone.list_indexes():
            self.logger.warning(f"Primary index {self.pinecone_config.primary_index} not found")
            self.create_optimized_pinecone_index(self.pinecone_config.primary_index)
        
        # Check secondary index
        if self.pinecone_config.secondary_index not in pinecone.list_indexes():
            self.logger.warning(f"Secondary index {self.pinecone_config.secondary_index} not found")
            self.create_optimized_pinecone_index(self.pinecone_config.secondary_index)
        
        # Verify index statistics
        for index_name in [self.pinecone_config.primary_index, self.pinecone_config.secondary_index]:
            index = pinecone.Index(index_name)
            stats = index.describe_index_stats()
            self.logger.info(f"Index {index_name} stats: {stats}")
    
    def create_optimized_pinecone_index(self, index_name: str):
        """Create optimized Pinecone index for business intelligence"""
        import pinecone
        
        pinecone.create_index(
            name=index_name,
            dimension=self.pinecone_config.dimension,
            metric=self.pinecone_config.metric,
            metadata_config=self.pinecone_config.metadata_config,
            pods=1,  # Start with 1 pod, scale as needed
            replicas=1,  # Add replicas for high availability
            pod_type="p1.x1"  # Performance optimized
        )
        
        self.logger.info(f"Created optimized Pinecone index: {index_name}")
    
    def setup_weaviate_schema(self):
        """Setup optimized Weaviate schema for Sophia AI"""
        
        # Define optimized schema for business intelligence
        schema = {
            "class": self.weaviate_config.class_name,
            "description": "Sophia AI Pay Ready business intelligence data",
            "vectorizer": self.weaviate_config.vectorizer,
            "moduleConfig": {
                self.weaviate_config.vectorizer: {
                    "model": "text-embedding-ada-002",
                    "modelVersion": "002",
                    "type": "text"
                },
                self.weaviate_config.generative_module: {
                    "model": "gpt-4"
                },
                self.weaviate_config.reranker_module: {
                    "model": "rerank-english-v2.0"
                }
            },
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Main content text",
                    "moduleConfig": {
                        self.weaviate_config.vectorizer: {
                            "skip": False,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "title",
                    "dataType": ["string"],
                    "description": "Document title",
                    "moduleConfig": {
                        self.weaviate_config.vectorizer: {
                            "skip": False,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "category",
                    "dataType": ["string"],
                    "description": "Business category (business, finance, operations, strategy)"
                },
                {
                    "name": "department",
                    "dataType": ["string"],
                    "description": "Department (sales, marketing, finance, hr, operations)"
                },
                {
                    "name": "priority",
                    "dataType": ["string"],
                    "description": "Priority level (high, medium, low)"
                },
                {
                    "name": "date_created",
                    "dataType": ["date"],
                    "description": "Creation date"
                },
                {
                    "name": "data_source",
                    "dataType": ["string"],
                    "description": "Source of data (slack, gong, internal_db, api_feed)"
                },
                {
                    "name": "confidence_score",
                    "dataType": ["number"],
                    "description": "Confidence score (0.0 to 1.0)"
                },
                {
                    "name": "business_unit",
                    "dataType": ["string"],
                    "description": "Business unit (pay_ready_core, pay_ready_plus, enterprise)"
                },
                {
                    "name": "metric_type",
                    "dataType": ["string"],
                    "description": "Type of metric (revenue, growth, efficiency, satisfaction)"
                },
                {
                    "name": "tags",
                    "dataType": ["string[]"],
                    "description": "Associated tags"
                }
            ],
            "vectorIndexConfig": {
                "skip": False,
                "cleanupIntervalSeconds": 300,
                "maxConnections": 64,
                "efConstruction": 128,
                "ef": -1,
                "dynamicEfMin": 100,
                "dynamicEfMax": 500,
                "dynamicEfFactor": 8,
                "vectorCacheMaxObjects": 1000000,
                "flatSearchCutoff": 40000,
                "distance": "cosine"
            },
            "invertedIndexConfig": {
                "bm25": {
                    "b": 0.75,
                    "k1": 1.2
                },
                "cleanupIntervalSeconds": 60,
                "stopwords": {
                    "preset": "en",
                    "additions": ["pay", "ready", "payready"],
                    "removals": ["business", "intelligence", "data"]
                }
            }
        }
        
        # Create or update schema
        try:
            existing_schema = self.weaviate_client.schema.get(self.weaviate_config.class_name)
            if existing_schema:
                self.logger.info(f"Schema for {self.weaviate_config.class_name} already exists")
            else:
                self.weaviate_client.schema.create_class(schema)
                self.logger.info(f"Created optimized Weaviate schema: {self.weaviate_config.class_name}")
        except Exception as e:
            self.logger.error(f"Failed to setup Weaviate schema: {str(e)}")
    
    def hybrid_search(self, query: str, limit: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Perform optimized hybrid search across Pinecone and Weaviate
        Combines vector similarity with metadata filtering and reranking
        """
        start_time = time.time()
        
        try:
            # Parallel search in both databases
            pinecone_results = self.search_pinecone(query, limit * 2, filters)
            weaviate_results = self.search_weaviate(query, limit * 2, filters)
            
            # Combine and rerank results
            combined_results = self.combine_and_rerank(
                pinecone_results, 
                weaviate_results, 
                query, 
                limit
            )
            
            # Update metrics
            latency = time.time() - start_time
            self.update_metrics("hybrid", latency)
            
            return combined_results
            
        except Exception as e:
            self.logger.error(f"Hybrid search failed: {str(e)}")
            self.metrics["error_count"] += 1
            raise
    
    def search_pinecone(self, query: str, limit: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Optimized Pinecone search with business intelligence focus"""
        import pinecone
        
        # Get query embedding (would use actual embedding service)
        query_vector = self.get_embedding(query)
        
        # Build metadata filter
        metadata_filter = self.build_pinecone_filter(filters) if filters else None
        
        # Search primary index
        index = pinecone.Index(self.pinecone_config.primary_index)
        results = index.query(
            vector=query_vector,
            top_k=limit,
            include_metadata=True,
            filter=metadata_filter
        )
        
        self.metrics["pinecone_queries"] += 1
        return self.format_pinecone_results(results)
    
    def search_weaviate(self, query: str, limit: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Optimized Weaviate search with generative capabilities"""
        
        # Build Weaviate query with hybrid search
        where_filter = self.build_weaviate_filter(filters) if filters else None
        
        query_builder = (
            self.weaviate_client.query
            .get(self.weaviate_config.class_name, [
                "content", "title", "category", "department", 
                "priority", "date_created", "confidence_score"
            ])
            .with_hybrid(query=query, alpha=0.7)  # 70% vector, 30% BM25
            .with_limit(limit)
        )
        
        if where_filter:
            query_builder = query_builder.with_where(where_filter)
        
        # Add generative search for business insights
        query_builder = query_builder.with_generate(
            single_prompt="Summarize this business intelligence data: {content}",
            grouped_task="Provide strategic insights based on these business metrics"
        )
        
        results = query_builder.do()
        
        self.metrics["weaviate_queries"] += 1
        return self.format_weaviate_results(results)
    
    def combine_and_rerank(self, pinecone_results: List, weaviate_results: List, 
                          query: str, limit: int) -> List[Dict[str, Any]]:
        """Intelligent combination and reranking of results"""
        
        # Combine results with source tracking
        combined = []
        
        # Add Pinecone results with weight
        for result in pinecone_results:
            result["source"] = "pinecone"
            result["weighted_score"] = result["score"] * 0.6  # 60% weight
            combined.append(result)
        
        # Add Weaviate results with weight
        for result in weaviate_results:
            result["source"] = "weaviate"
            result["weighted_score"] = result["score"] * 0.4  # 40% weight
            combined.append(result)
        
        # Remove duplicates based on content similarity
        deduplicated = self.deduplicate_results(combined)
        
        # Sort by weighted score
        deduplicated.sort(key=lambda x: x["weighted_score"], reverse=True)
        
        # Apply business intelligence specific reranking
        reranked = self.business_intelligence_rerank(deduplicated, query)
        
        return reranked[:limit]
    
    def business_intelligence_rerank(self, results: List[Dict], query: str) -> List[Dict]:
        """Apply business intelligence specific reranking logic"""
        
        # Define business priority weights
        priority_weights = {
            "high": 1.3,
            "medium": 1.0,
            "low": 0.8
        }
        
        category_weights = {
            "finance": 1.2,
            "strategy": 1.2,
            "operations": 1.1,
            "business": 1.0
        }
        
        # Apply weights
        for result in results:
            metadata = result.get("metadata", {})
            
            # Priority boost
            priority = metadata.get("priority", "medium")
            result["weighted_score"] *= priority_weights.get(priority, 1.0)
            
            # Category boost
            category = metadata.get("category", "business")
            result["weighted_score"] *= category_weights.get(category, 1.0)
            
            # Recency boost (more recent = higher score)
            date_created = metadata.get("date_created")
            if date_created:
                # Add recency calculation logic here
                pass
            
            # Confidence boost
            confidence = metadata.get("confidence_score", 0.5)
            result["weighted_score"] *= (0.5 + confidence * 0.5)
        
        # Re-sort after reranking
        results.sort(key=lambda x: x["weighted_score"], reverse=True)
        return results
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text (placeholder - implement with actual service)"""
        # This would integrate with OpenAI, Cohere, or other embedding service
        # For now, return dummy vector
        return [0.0] * self.pinecone_config.dimension
    
    def build_pinecone_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build Pinecone metadata filter"""
        pinecone_filter = {}
        
        for key, value in filters.items():
            if key in self.pinecone_config.metadata_config["indexed"]:
                if isinstance(value, list):
                    pinecone_filter[key] = {"$in": value}
                else:
                    pinecone_filter[key] = {"$eq": value}
        
        return pinecone_filter
    
    def build_weaviate_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build Weaviate where filter"""
        where_conditions = []
        
        for key, value in filters.items():
            if isinstance(value, list):
                where_conditions.append({
                    "path": [key],
                    "operator": "ContainsAny",
                    "valueStringArray": value
                })
            else:
                where_conditions.append({
                    "path": [key],
                    "operator": "Equal",
                    "valueString": str(value)
                })
        
        if len(where_conditions) == 1:
            return where_conditions[0]
        elif len(where_conditions) > 1:
            return {
                "operator": "And",
                "operands": where_conditions
            }
        
        return {}
    
    def format_pinecone_results(self, results) -> List[Dict[str, Any]]:
        """Format Pinecone results for consistency"""
        formatted = []
        
        for match in results.get("matches", []):
            formatted.append({
                "id": match["id"],
                "score": match["score"],
                "content": match.get("metadata", {}).get("content", ""),
                "metadata": match.get("metadata", {})
            })
        
        return formatted
    
    def format_weaviate_results(self, results) -> List[Dict[str, Any]]:
        """Format Weaviate results for consistency"""
        formatted = []
        
        data = results.get("data", {}).get("Get", {}).get(self.weaviate_config.class_name, [])
        
        for item in data:
            formatted.append({
                "id": item.get("_additional", {}).get("id", ""),
                "score": item.get("_additional", {}).get("score", 0.0),
                "content": item.get("content", ""),
                "metadata": {
                    "title": item.get("title", ""),
                    "category": item.get("category", ""),
                    "department": item.get("department", ""),
                    "priority": item.get("priority", ""),
                    "confidence_score": item.get("confidence_score", 0.0)
                },
                "generated": item.get("_additional", {}).get("generate", {})
            })
        
        return formatted
    
    def deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on content similarity"""
        # Simple deduplication based on content hash
        # In production, would use more sophisticated similarity detection
        seen_content = set()
        deduplicated = []
        
        for result in results:
            content_hash = hash(result.get("content", "")[:100])  # First 100 chars
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                deduplicated.append(result)
        
        return deduplicated
    
    def update_metrics(self, query_type: str, latency: float):
        """Update performance metrics"""
        self.metrics[f"{query_type}_queries"] += 1
        
        # Update average latency
        total_queries = sum([
            self.metrics["pinecone_queries"],
            self.metrics["weaviate_queries"], 
            self.metrics["hybrid_queries"]
        ])
        
        self.metrics["avg_latency"] = (
            (self.metrics["avg_latency"] * (total_queries - 1) + latency) / total_queries
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.copy()
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for both vector databases"""
        health_status = {
            "pinecone": {"status": "unknown", "latency": None, "error": None},
            "weaviate": {"status": "unknown", "latency": None, "error": None}
        }
        
        # Test Pinecone
        try:
            start_time = time.time()
            import pinecone
            index = pinecone.Index(self.pinecone_config.primary_index)
            stats = index.describe_index_stats()
            latency = time.time() - start_time
            
            health_status["pinecone"] = {
                "status": "healthy",
                "latency": latency,
                "stats": stats,
                "error": None
            }
        except Exception as e:
            health_status["pinecone"] = {
                "status": "unhealthy",
                "latency": None,
                "error": str(e)
            }
        
        # Test Weaviate
        try:
            start_time = time.time()
            meta = self.weaviate_client.get_meta()
            latency = time.time() - start_time
            
            health_status["weaviate"] = {
                "status": "healthy",
                "latency": latency,
                "version": meta.get("version"),
                "error": None
            }
        except Exception as e:
            health_status["weaviate"] = {
                "status": "unhealthy",
                "latency": None,
                "error": str(e)
            }
        
        return health_status

# Example usage and configuration
def create_optimized_vector_config():
    """Create optimized vector database configuration for Sophia AI"""
    
    pinecone_config = PineconeConfig(
        api_key="pcsk_7PHV2G_Mj1rRCwiHZ7YsuuzJcqKch9akzNKXv6mfwDX65DenD8Q72w3Qjh4AmuataTnEDW",
        environment="us-west-2"
    )
    
    weaviate_config = WeaviateConfig(
        url="https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud",
        api_key="VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf"
    )
    
    return OptimizedVectorDatabaseManager(pinecone_config, weaviate_config)

if __name__ == "__main__":
    # Initialize optimized vector database manager
    vector_manager = create_optimized_vector_config()
    
    # Perform health check
    health = vector_manager.health_check()
    print("Vector Database Health Check:")
    print(json.dumps(health, indent=2))
    
    # Example hybrid search
    results = vector_manager.hybrid_search(
        query="Pay Ready revenue growth Q4 2024",
        limit=5,
        filters={
            "category": "finance",
            "priority": "high",
            "business_unit": "pay_ready_core"
        }
    )
    
    print(f"\\nFound {len(results)} results")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['metadata'].get('title', 'No title')} (Score: {result['weighted_score']:.3f})")

