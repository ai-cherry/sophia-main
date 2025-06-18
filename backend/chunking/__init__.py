"""
Sophia AI - Advanced Chunking Module
Comprehensive metadata extraction and chunking for business intelligence
"""

from .sophia_chunking_pipeline import SophiaChunkingPipeline, SophiaEnhancedMetadata
from .speaker_boundary_chunker import SpeakerBoundaryChunker
from .business_intelligence_extractor import BusinessIntelligenceExtractor
from .ai_agent_integration import AIAgentIntegration

__all__ = [
    "SophiaChunkingPipeline",
    "SophiaEnhancedMetadata", 
    "SpeakerBoundaryChunker",
    "BusinessIntelligenceExtractor",
    "AIAgentIntegration"
] 