"""
AI Memory MCP Server
MCP server for AI coding assistant memory system, refactored to use the BaseMCPServer.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.types import (
    CallToolRequest,
    ListResourcesRequest,
    ListToolsRequest,
    ReadResourceRequest,
    Resource,
    TextContent,
    Tool,
)

from backend.core.comprehensive_memory_manager import (
    MemoryOperationType,
    MemoryRequest,
    comprehensive_memory_manager,
)
from backend.mcp.base_mcp_server import BaseMCPServer, setup_logging

# Import dependencies with fallback
try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    pinecone = None
    Pinecone = None
    ServerlessSpec = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

class AIMemoryMCPServer(BaseMCPServer):
    """
    MCP Server for AI coding assistant memory system.
    Provides persistent memory storage and retrieval for development context.
    """

    def __init__(self):
        super().__init__("ai_memory")
        self.pc = None
        self.index = None
        self.encoder = None
        self.index_name = "sophia-ai-memory"
        self.dimension = 384  # all-MiniLM-L6-v2 embedding dimension

    async def initialize_integration(self):
        """Initializes the Pinecone and SentenceTransformer integration."""
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone is not available. Please install pinecone-client.")

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("SentenceTransformers is not available. Please install sentence-transformers.")

        try:
            # Initialize Pinecone
            api_key = os.getenv("PINECONE_API_KEY")
            if not api_key:
                self.logger.warning("PINECONE_API_KEY not found. Using dummy client.")
                self.pc = None
                self.index = None
            else:
                self.pc = Pinecone(api_key=api_key)

                # Create index if it doesn't exist
                if self.index_name not in self.pc.list_indexes().names():
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=self.dimension,
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud="aws",
                            region="us-east-1"
                        )
                    )
                    self.logger.info(f"Created Pinecone index: {self.index_name}")

                self.index = self.pc.Index(self.index_name)
                self.logger.info(f"Connected to Pinecone index: {self.index_name}")

            # Initialize sentence transformer
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            self.logger.info("Initialized SentenceTransformer encoder")

            # Set integration client for base class compatibility
            self.integration_client = self

        except Exception as e:
            self.logger.error(f"Failed to initialize AI Memory integration: {e}")
            raise

    async def list_resources(self, request: ListResourcesRequest) -> List[Resource]:
        """Lists available AI Memory resources."""
        return [
            Resource(
                uri="ai_memory://health",
                name="AI Memory Health Status",
                description="Current health and status of the AI Memory system.",
                mimeType="application/json"
            ),
            Resource(
                uri="ai_memory://stats",
                name="AI Memory Statistics",
                description="Statistics about stored memories and usage.",
                mimeType="application/json"
            )
        ]

    async def get_resource(self, request: ReadResourceRequest) -> str:
        """Gets a specific AI Memory resource."""
        uri = request.uri

        if uri == "ai_memory://health":
            health_status = {
                "status": "healthy" if self.index is not None else "degraded",
                "pinecone_connected": self.index is not None,
                "encoder_loaded": self.encoder is not None,
                "index_name": self.index_name,
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(health_status)

        elif uri == "ai_memory://stats":
            if self.index:
                try:
                    stats = self.index.describe_index_stats()
                    return json.dumps({
                        "total_vectors": stats.total_vector_count,
                        "index_fullness": stats.index_fullness,
                        "dimension": self.dimension,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    return json.dumps({"error": f"Failed to get stats: {e}"})
            else:
                return json.dumps({"error": "Pinecone index not available"})

        else:
            return json.dumps({"error": f"Unknown resource: {uri}"})

    async def list_tools(self, request: ListToolsRequest) -> List[Tool]:
        """Lists available AI Memory tools."""
        return [
            Tool(
                name="store_conversation",
                description="Store a conversation or development context in AI memory for future reference",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "conversation_text": {
                            "type": "string",
                            "description": "The conversation or context text to store"
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context about the conversation (e.g., 'bug fix', 'architecture decision')"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags to categorize the memory (e.g., ['python', 'debugging', 'api'])"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["conversation", "code_decision", "bug_solution", "architecture", "workflow", "requirement", "pattern", "api_usage"],
                            "description": "Category of the memory"
                        }
                    },
                    "required": ["conversation_text"]
                }
            ),
            Tool(
                name="recall_memory",
                description="Search and recall previous conversations and development context from AI memory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find relevant memories"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["conversation", "code_decision", "bug_solution", "architecture", "workflow", "requirement", "pattern", "api_usage"],
                            "description": "Filter by category (optional)"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by tags (optional)"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of memories to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="delete_memory",
                description="Delete a specific memory by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "ID of the memory to delete"
                        }
                    },
                    "required": ["memory_id"]
                }
            )
        ]

    async def call_tool(self, request: CallToolRequest) -> List[TextContent]:
        """Handles AI Memory tool calls."""
        tool_name = request.params.name
        arguments = request.params.arguments or {}

        try:
            if tool_name == "store_conversation":
                result = await self._store_conversation(arguments)
            elif tool_name == "recall_memory":
                result = await self._recall_memory(arguments)
            elif tool_name == "delete_memory":
                result = await self._delete_memory(arguments)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            return [TextContent(type="text", text=json.dumps(result))]

        except Exception as e:
            self.logger.error(f"Error in tool call {tool_name}: {e}")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    async def _store_conversation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Store a conversation in AI memory."""
        conversation_text = args.get("conversation_text", "")
        context = args.get("context", "")
        tags = args.get("tags", [])
        category = args.get("category", "conversation")

        if not conversation_text:
            return {"error": "conversation_text is required"}

        if not self.encoder:
            return {"error": "Encoder not available"}

        try:
            # Generate embedding
            embedding = self.encoder.encode(conversation_text).tolist()

            # Create memory record
            memory_id = str(uuid.uuid4())
            metadata = {
                "text": conversation_text,
                "context": context,
                "tags": tags,
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "source": "ai_memory_mcp"
            }

            # Store in Pinecone if available
            if self.index:
                memory_request = MemoryRequest(operation=MemoryOperationType.STORE, content=[(memory_id, embedding, metadata)])
                await comprehensive_memory_manager.process_memory_request(memory_request)

            return {
                "success": True,
                "memory_id": memory_id,
                "category": category,
                "tags": tags,
                "timestamp": metadata["timestamp"]
            }

        except Exception as e:
            self.logger.error(f"Error storing conversation: {e}")
            return {"error": f"Failed to store conversation: {e}"}

    async def _recall_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Recall memories from AI memory."""
        query = args.get("query", "")
        category = args.get("category")
        tags = args.get("tags", [])
        top_k = args.get("top_k", 5)

        if not query:
            return {"error": "query is required"}

        if not self.encoder:
            return {"error": "Encoder not available"}

        if not self.index:
            return {"error": "Pinecone index not available"}

        try:
            # Generate query embedding
            query_embedding = self.encoder.encode(query).tolist()

            # Build filter
            filter_dict = {}
            if category:
                filter_dict["category"] = category
            if tags:
                filter_dict["tags"] = {"$in": tags}

            # Search in Pinecone
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )

            # Format results
            memories = []
            for match in search_results.matches:
                memory = {
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "context": match.metadata.get("context", ""),
                    "category": match.metadata.get("category", ""),
                    "tags": match.metadata.get("tags", []),
                    "timestamp": match.metadata.get("timestamp", "")
                }
                memories.append(memory)

            return {
                "success": True,
                "query": query,
                "count": len(memories),
                "memories": memories
            }

        except Exception as e:
            self.logger.error(f"Error recalling memories: {e}")
            return {"error": f"Failed to recall memories: {e}"}

    async def _delete_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a memory by ID."""
        memory_id = args.get("memory_id", "")

        if not memory_id:
            return {"error": "memory_id is required"}

        if not self.index:
            return {"error": "Pinecone index not available"}

        try:
            await comprehensive_memory_manager.process_memory_request(MemoryRequest(operation=MemoryOperationType.DELETE, ids=[memory_id]))
            return {
                "success": True,
                "memory_id": memory_id,
                "message": "Memory deleted successfully"
            }

        except Exception as e:
            self.logger.error(f"Error deleting memory: {e}")
            return {"error": f"Failed to delete memory: {e}"}


async def main():
    """Main entry point for the AI Memory MCP server."""
    setup_logging()
    server = AIMemoryMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
