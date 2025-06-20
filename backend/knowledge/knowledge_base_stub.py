"""Simple stub for SophiaKnowledgeBase to avoid import errors"""

from typing import Any, Dict


class SophiaKnowledgeBase:
    """Stub implementation of SophiaKnowledgeBase"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize stub knowledge base"""
        self.config = config

    def search(self, query: str) -> Dict[str, Any]:
        """Stub search method"""
        return {"results": [], "query": query, "status": "stub_implementation"}
