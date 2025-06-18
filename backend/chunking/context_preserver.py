"""
Sophia AI - Context Preserver
Preserve conversation context across chunks
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ContextPreserver:
    """Preserve conversation context across chunks"""
    
    def __init__(self):
        self.context_window = 5  # Number of chunks to preserve context
        self.context_cache = {}
        
        logger.info("Context Preserver initialized")
    
    async def preserve_context(
        self, 
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Preserve conversation context for each chunk"""
        
        enhanced_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Get context from surrounding chunks
            context_before = self._get_context_before(chunks, i)
            context_after = self._get_context_after(chunks, i)
            
            # Create conversation summary
            conversation_summary = self._create_conversation_summary(
                context_before, chunk, context_after
            )
            
            enhanced_chunk = {
                **chunk,
                "conversation_context": {
                    "context_before": context_before,
                    "context_after": context_after,
                    "conversation_summary": conversation_summary,
                    "context_window": self.context_window
                },
                "full_context_available": len(context_before) + len(context_after) > 0
            }
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def _get_context_before(self, chunks: List[Dict[str, Any]], current_index: int) -> List[Dict[str, Any]]:
        """Get context chunks before current position"""
        
        start_index = max(0, current_index - self.context_window)
        context_chunks = []
        
        for i in range(start_index, current_index):
            if i < len(chunks):
                context_chunks.append({
                    "text": chunks[i].get("text", ""),
                    "speaker": chunks[i].get("speaker"),
                    "chunk_type": chunks[i].get("chunk_type", "unknown")
                })
        
        return context_chunks
    
    def _get_context_after(self, chunks: List[Dict[str, Any]], current_index: int) -> List[Dict[str, Any]]:
        """Get context chunks after current position"""
        
        end_index = min(len(chunks), current_index + self.context_window + 1)
        context_chunks = []
        
        for i in range(current_index + 1, end_index):
            if i < len(chunks):
                context_chunks.append({
                    "text": chunks[i].get("text", ""),
                    "speaker": chunks[i].get("speaker"),
                    "chunk_type": chunks[i].get("chunk_type", "unknown")
                })
        
        return context_chunks
    
    def _create_conversation_summary(
        self, 
        context_before: List[Dict[str, Any]], 
        current_chunk: Dict[str, Any],
        context_after: List[Dict[str, Any]]
    ) -> str:
        """Create a summary of the conversation context"""
        
        summary_parts = []
        
        # Add context before
        if context_before:
            speakers_before = set(chunk.get("speaker") for chunk in context_before if chunk.get("speaker"))
            if speakers_before:
                summary_parts.append(f"Previous speakers: {', '.join(speakers_before)}")
        
        # Add current chunk info
        current_speaker = current_chunk.get("speaker")
        if current_speaker:
            summary_parts.append(f"Current speaker: {current_speaker}")
        
        # Add context after
        if context_after:
            speakers_after = set(chunk.get("speaker") for chunk in context_after if chunk.get("speaker"))
            if speakers_after:
                summary_parts.append(f"Following speakers: {', '.join(speakers_after)}")
        
        return ". ".join(summary_parts) if summary_parts else "No context available" 