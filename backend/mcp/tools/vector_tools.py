import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

from ..sophia_mcp_server import MCPTool
from ...core.secret_manager import secret_manager

class VectorSearchTool(MCPTool):
    """Tool for searching vector databases"""
    
    def __init__(self):
        super().__init__(
            name="vector_search",
            description="Search for similar vectors in a vector database",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Query text to search for",
                    "required": True
                },
                "collection": {
                    "type": "string",
                    "description": "Collection or namespace to search in",
                    "required": False
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "required": False,
                    "default": 5
                },
                "vector_db": {
                    "type": "string",
                    "description": "Vector database to use",
                    "enum": ["pinecone", "weaviate"],
                    "required": False
                },
                "filter": {
                    "type": "object",
                    "description": "Filter to apply to the search",
                    "required": False
                }
            }
        )
        self.logger = logging.getLogger(__name__)
        self.openai_client = None
        self.pinecone_client = None
        self.weaviate_client = None
        
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the provided parameters"""
        # Get parameters
        query = parameters["query"]
        collection = parameters.get("collection")
        limit = parameters.get("limit", 5)
        vector_db = parameters.get("vector_db")
        filter_obj = parameters.get("filter")
        
        # Determine vector database to use
        if not vector_db:
            vector_db = os.environ.get("VECTOR_DB", "pinecone")
        
        try:
            # Generate embedding for query
            embedding = await self._generate_embedding(query)
            
            # Perform search based on vector database
            if vector_db == "pinecone":
                results = await self._search_pinecone(embedding, collection, limit, filter_obj)
            elif vector_db == "weaviate":
                results = await self._search_weaviate(embedding, collection, limit, filter_obj)
            else:
                raise ValueError(f"Unsupported vector database: {vector_db}")
            
            # Prepare response
            response = {
                "query": query,
                "vector_db": vector_db,
                "results": results,
                "metadata": {
                    "collection": collection,
                    "limit": limit,
                    "filter": filter_obj,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error searching vector database: {e}")
            return {
                "error": str(e),
                "query": query
            }
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not self.openai_client:
            from openai import OpenAI
            api_key = await secret_manager.get_secret("api_key", "openai")
            self.openai_client = OpenAI(api_key=api_key)
        
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        
        return response.data[0].embedding
    
    async def _search_pinecone(self, embedding: List[float], namespace: Optional[str], limit: int, filter_obj: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search Pinecone vector database"""
        if not self.pinecone_client:
            import pinecone
            
            api_key = await secret_manager.get_secret("api_key", "pinecone")
            environment = os.environ.get("PINECONE_ENVIRONMENT", "us-east1-gcp")
            
            pinecone.init(api_key=api_key, environment=environment)
            
            index_name = os.environ.get("PINECONE_INDEX", "sophia-index")
            self.pinecone_client = pinecone.Index(index_name)
        
        # Perform query
        query_response = self.pinecone_client.query(
            vector=embedding,
            top_k=limit,
            namespace=namespace,
            filter=filter_obj,
            include_metadata=True
        )
        
        # Format results
        results = []
        for match in query_response.matches:
            result = {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata
            }
            results.append(result)
        
        return results
    
    async def _search_weaviate(self, embedding: List[float], class_name: Optional[str], limit: int, filter_obj: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search Weaviate vector database"""
        if not self.weaviate_client:
            import weaviate
            
            api_key = await secret_manager.get_secret("api_key", "weaviate")
            url = os.environ.get("WEAVIATE_URL", "http://localhost:8080")
            
            self.weaviate_client = weaviate.Client(
                url=url,
                auth_client_secret=weaviate.AuthApiKey(api_key=api_key)
            )
        
        # Determine class name if not provided
        if not class_name:
            # Get first class from schema
            schema = self.weaviate_client.schema.get()
            if schema and "classes" in schema and schema["classes"]:
                class_name = schema["classes"][0]["class"]
            else:
                raise ValueError("No class name provided and no classes found in schema")
        
        # Build query
        query = (
            self.weaviate_client.query
            .get(class_name, ["id", "text", "source", "created", "metadata"])
            .with_near_vector({
                "vector": embedding
            })
            .with_limit(limit)
            .with_additional(["certainty"])
        )
        
        # Add filter if provided
        if filter_obj:
            where_filter = self._convert_filter_to_weaviate(filter_obj)
            query = query.with_where(where_filter)
        
        # Execute query
        result = query.do()
        
        # Format results
        results = []
        if "data" in result and "Get" in result["data"] and class_name in result["data"]["Get"]:
            for item in result["data"]["Get"][class_name]:
                result_item = {
                    "id": item.get("id"),
                    "score": item.get("_additional", {}).get("certainty"),
                    "metadata": {
                        "text": item.get("text"),
                        "source": item.get("source"),
                        "created": item.get("created")
                    }
                }
                
                # Add any additional metadata
                if "metadata" in item and isinstance(item["metadata"], dict):
                    result_item["metadata"].update(item["metadata"])
                
                results.append(result_item)
        
        return results
    
    def _convert_filter_to_weaviate(self, filter_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Convert generic filter to Weaviate filter format"""
        if not filter_obj:
            return {}
        
        # Simple conversion for basic filters
        weaviate_filter = {}
        
        # Handle basic equality filters
        for key, value in filter_obj.items():
            if isinstance(value, (str, int, float, bool)):
                weaviate_filter = {
                    "path": [key],
                    "operator": "Equal",
                    "valueString": str(value) if isinstance(value, str) else None,
                    "valueInt": value if isinstance(value, int) else None,
                    "valueNumber": value if isinstance(value, float) else None,
                    "valueBoolean": value if isinstance(value, bool) else None
                }
                
                # Remove None values
                weaviate_filter = {k: v for k, v in weaviate_filter.items() if v is not None}
        
        return weaviate_filter

class VectorStoreTool(MCPTool):
    """Tool for storing data in vector databases"""
    
    def __init__(self):
        super().__init__(
            name="vector_store",
            description="Store data in a vector database",
            parameters={
                "text": {
                    "type": "string",
                    "description": "Text to store",
                    "required": True
                },
                "metadata": {
                    "type": "object",
                    "description": "Metadata to store with the text",
                    "required": False
                },
                "collection": {
                    "type": "string",
                    "description": "Collection or namespace to store in",
                    "required": False
                },
                "vector_db": {
                    "type": "string",
                    "description": "Vector database to use",
                    "enum": ["pinecone", "weaviate"],
                    "required": False
                },
                "id": {
                    "type": "string",
                    "description": "ID to use for the stored item (if not provided, one will be generated)",
                    "required": False
                }
            }
        )
        self.logger = logging.getLogger(__name__)
        self.openai_client = None
        self.pinecone_client = None
        self.weaviate_client = None
        
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the provided parameters"""
        # Get parameters
        text = parameters["text"]
        metadata = parameters.get("metadata", {})
        collection = parameters.get("collection")
        vector_db = parameters.get("vector_db")
        item_id = parameters.get("id")
        
        # Determine vector database to use
        if not vector_db:
            vector_db = os.environ.get("VECTOR_DB", "pinecone")
        
        try:
            # Generate embedding for text
            embedding = await self._generate_embedding(text)
            
            # Store data based on vector database
            if vector_db == "pinecone":
                result = await self._store_pinecone(text, embedding, metadata, collection, item_id)
            elif vector_db == "weaviate":
                result = await self._store_weaviate(text, embedding, metadata, collection, item_id)
            else:
                raise ValueError(f"Unsupported vector database: {vector_db}")
            
            # Prepare response
            response = {
                "success": True,
                "vector_db": vector_db,
                "id": result.get("id"),
                "metadata": {
                    "collection": collection,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error storing in vector database: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not self.openai_client:
            from openai import OpenAI
            api_key = await secret_manager.get_secret("api_key", "openai")
            self.openai_client = OpenAI(api_key=api_key)
        
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        
        return response.data[0].embedding
    
    async def _store_pinecone(self, text: str, embedding: List[float], metadata: Dict[str, Any], namespace: Optional[str], item_id: Optional[str]) -> Dict[str, Any]:
        """Store data in Pinecone vector database"""
        if not self.pinecone_client:
            import pinecone
            import uuid
            
            api_key = await secret_manager.get_secret("api_key", "pinecone")
            environment = os.environ.get("PINECONE_ENVIRONMENT", "us-east1-gcp")
            
            pinecone.init(api_key=api_key, environment=environment)
            
            index_name = os.environ.get("PINECONE_INDEX", "sophia-index")
            self.pinecone_client = pinecone.Index(index_name)
        
        # Generate ID if not provided
        if not item_id:
            import uuid
            item_id = str(uuid.uuid4())
        
        # Add text to metadata
        full_metadata = {
            "text": text,
            "created": datetime.now().isoformat(),
            **metadata
        }
        
        # Upsert vector
        self.pinecone_client.upsert(
            vectors=[(item_id, embedding, full_metadata)],
            namespace=namespace
        )
        
        return {
            "id": item_id
        }
    
    async def _store_weaviate(self, text: str, embedding: List[float], metadata: Dict[str, Any], class_name: Optional[str], item_id: Optional[str]) -> Dict[str, Any]:
        """Store data in Weaviate vector database"""
        if not self.weaviate_client:
            import weaviate
            
            api_key = await secret_manager.get_secret("api_key", "weaviate")
            url = os.environ.get("WEAVIATE_URL", "http://localhost:8080")
            
            self.weaviate_client = weaviate.Client(
                url=url,
                auth_client_secret=weaviate.AuthApiKey(api_key=api_key)
            )
        
        # Determine class name if not provided
        if not class_name:
            class_name = os.environ.get("WEAVIATE_DEFAULT_CLASS", "SophiaData")
            
            # Check if class exists, create if not
            if not self.weaviate_client.schema.contains(class_name):
                class_obj = {
                    "class": class_name,
                    "vectorizer": "none",  # We'll provide our own vectors
                    "properties": [
                        {
                            "name": "text",
                            "dataType": ["text"]
                        },
                        {
                            "name": "source",
                            "dataType": ["string"]
                        },
                        {
                            "name": "created",
                            "dataType": ["date"]
                        },
                        {
                            "name": "metadata",
                            "dataType": ["object"]
                        }
                    ]
                }
                
                self.weaviate_client.schema.create_class(class_obj)
        
        # Prepare data object
        data_object = {
            "text": text,
            "source": metadata.get("source", "api"),
            "created": datetime.now().isoformat(),
            "metadata": metadata
        }
        
        # Create object with vector
        if item_id:
            # Use provided ID
            result = self.weaviate_client.data_object.create(
                class_name=class_name,
                data_object=data_object,
                vector=embedding,
                uuid=item_id
            )
        else:
            # Generate ID
            result = self.weaviate_client.data_object.create(
                class_name=class_name,
                data_object=data_object,
                vector=embedding
            )
        
        return {
            "id": result
        }
