"""Hugging Face Integration for Sophia AI
Connects to the official Hugging Face MCP Server to provide access to models,
datasets, Spaces, and papers.
"""

import logging
from typing import Any, Dict, List, Optional

from backend.mcp.mcp_client import MCPClient
from infrastructure.esc.huggingface_secrets import huggingface_secret_manager

logger = logging.getLogger(__name__)


class HuggingFaceIntegration:
    """A client that connects to and interacts with the Hugging Face MCP server."""

    HF_MCP_URL = "https://hf.co/mcp"

    def __init__(self):
        self.client: Optional[MCPClient] = None
        self.tools: Dict[str, Any] = {}
        self.initialized = False

    async def initialize(self):
        """Initializes the connection to the Hugging Face MCP server."""
        if self.initialized:
            return

        logger.info("Initializing Hugging Face integration...")
        try:
            api_key = await huggingface_secret_manager.get_huggingface_api_key()
            self.client = MCPClient(token=api_key)

            # Connect to the official HF MCP server
            await self.client.add_mcp_server("http", url=self.HF_MCP_URL)
            self.tools = self.client.get_tools()

            self.initialized = True
            logger.info(
                f"Successfully connected to Hugging Face MCP server. Found {len(self.tools)} tools."
            )

        except Exception as e:
            logger.error(
                f"Failed to initialize Hugging Face integration: {e}", exc_info=True
            )
            self.initialized = False

    async def search_models(
        self, query: str, top_k: int = 5, tags: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Searches for models on the Hugging Face Hub.

        Args:
            query: The natural language search query.
            top_k: The number of models to return.
            tags: A list of tags to filter by (e.g., 'text-generation').

        Returns:
            A list of dictionaries, each representing a found model.
        """
        if not self.initialized:
            await self.initialize()

        try:
            # The actual tool name and parameters would be discovered from self.tools,
            # but we can implement the common case directly.
            result = await self.client.call_tool(
                "search-models", query=query, limit=top_k, tags=tags or []
            )
            return result.content
        except Exception as e:
            logger.error(f"Error searching models: {e}")
            return [{"error": str(e)}]

    async def get_paper_details(self, paper_id: str) -> Dict[str, Any]:
        """Gets details for a paper, typically from arXiv.

        Args:
            paper_id: The ID of the paper (e.g., '2404.19756').

        Returns:
            A dictionary containing the paper's details.
        """
        if not self.initialized:
            await self.initialize()

        try:
            result = await self.client.call_tool("get-paper-info", paper_id=paper_id)
            return result.content
        except Exception as e:
            logger.error(f"Error getting paper details: {e}")
            return {"error": str(e)}

    async def run_space_tool(self, space_id: str, **kwargs) -> Any:
        """Executes a tool hosted in a Hugging Face Space.

        Args:
            space_id: The ID of the Space (e.g., 'espnet/siddhant_multi_ling_tts').
            **kwargs: The parameters to pass to the Space's tool.

        Returns:
            The output from the Space tool.
        """
        if not self.initialized:
            await self.initialize()

        try:
            # The tool name for a space is often the space_id itself or a derivative.
            # This is a simplified call; a real implementation might need to
            # look up the exact tool name from the space's metadata.
            result = await self.client.call_tool(space_id, **kwargs)
            return result.content
        except Exception as e:
            logger.error(f"Error running Space tool '{space_id}': {e}")
            return {"error": str(e)}


# Global instance for easy access
huggingface_integration = HuggingFaceIntegration()
