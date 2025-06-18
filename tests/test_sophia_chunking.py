"""
Tests for Sophia AI Chunking Pipeline
"""

import pytest
import asyncio
from backend.chunking import SophiaChunkingPipeline

@pytest.fixture
def chunking_pipeline():
    """Create a chunking pipeline instance for testing"""
    return SophiaChunkingPipeline()

@pytest.fixture
def sample_gong_transcript():
    """Sample Gong call transcript for testing"""
    return """
John Smith: Hi Sarah, thanks for taking the call today. I wanted to discuss the pricing for the Pay Ready platform.

Sarah Johnson: Of course, John. I'm happy to go through the pricing with you. We have several options depending on your needs.

John Smith: Great. We're looking at about 500 units across 3 properties, so we need something that can scale.

Sarah Johnson: Perfect. For that scale, I'd recommend our Pay Ready Plus plan at $2.50 per unit per month. That would be about $1,250 monthly.

John Smith: That sounds reasonable. What about the implementation timeline?

Sarah Johnson: We can typically get you up and running within 2-3 weeks. The API integration is straightforward.

John Smith: Excellent. I think we're ready to move forward. Can you send over the contract?

Sarah Johnson: Absolutely! I'll have that sent to you by end of day. We're excited to have you on board.
"""

@pytest.fixture
def sample_slack_message():
    """Sample Slack message for testing"""
    return """
Urgent: Client Acme Corp is having issues with the API integration. 
They're getting 500 errors and need immediate support. 
This is a $50k account that we can't afford to lose.
"""

@pytest.mark.asyncio
async def test_gong_transcript_chunking(chunking_pipeline, sample_gong_transcript):
    """Test chunking of Gong call transcript"""
    
    chunks = await chunking_pipeline.process_content(
        content=sample_gong_transcript,
        content_type="gong_call",
        source_id="test_call_123",
        priority="normal"
    )
    
    assert len(chunks) > 0
    
    # Check that chunks have required metadata
    for chunk in chunks:
        assert "text" in chunk
        assert "metadata" in chunk
        assert "chunk_type" in chunk
        
        metadata = chunk["metadata"]
        assert "chunk_id" in metadata
        assert "content_type" in metadata
        assert "speaker" in metadata
        assert "primary_topic" in metadata
        assert "sentiment_score" in metadata

@pytest.mark.asyncio
async def test_slack_message_chunking(chunking_pipeline, sample_slack_message):
    """Test chunking of Slack message"""
    
    chunks = await chunking_pipeline.process_content(
        content=sample_slack_message,
        content_type="slack_message",
        source_id="test_message_456",
        priority="high"
    )
    
    assert len(chunks) > 0
    
    # Check that high priority messages are processed in realtime mode
    for chunk in chunks:
        metadata = chunk["metadata"]
        assert metadata["processing_mode"] in ["realtime", "enhanced"]

@pytest.mark.asyncio
async def test_business_intelligence_extraction(chunking_pipeline):
    """Test business intelligence extraction"""
    
    test_content = """
    We need to discuss the $25,000 implementation project for the new API integration.
    The client is concerned about the timeline and wants to proceed with the contract.
    This is a high-priority deal that could lead to additional $100k in revenue.
    """
    
    chunks = await chunking_pipeline.process_content(
        content=test_content,
        content_type="document",
        source_id="test_doc_789",
        priority="normal"
    )
    
    assert len(chunks) > 0
    
    # Check for business intelligence extraction
    for chunk in chunks:
        metadata = chunk["metadata"]
        assert "revenue_potential" in metadata
        assert "technology_relevance" in metadata
        assert "performance_impact" in metadata
        
        # Should detect high revenue potential
        assert metadata["revenue_potential"] > 0

@pytest.mark.asyncio
async def test_decision_point_detection(chunking_pipeline):
    """Test decision point detection"""
    
    test_content = """
    John: I think we should go with the Pay Ready Plus plan.
    Sarah: That sounds good to me. Let's proceed with the contract.
    John: Perfect. We've decided to move forward with this.
    """
    
    chunks = await chunking_pipeline.process_content(
        content=test_content,
        content_type="gong_call",
        source_id="test_decision_call",
        priority="normal"
    )
    
    # Should detect decision points
    decision_chunks = [c for c in chunks if c.get("chunk_type") == "decision_point"]
    assert len(decision_chunks) > 0

@pytest.mark.asyncio
async def test_context_preservation(chunking_pipeline):
    """Test conversation context preservation"""
    
    test_content = """
    Speaker A: Let's discuss the pricing.
    Speaker B: Sure, what's your budget?
    Speaker A: We're looking at around $10k per month.
    Speaker B: That works for us.
    """
    
    chunks = await chunking_pipeline.process_content(
        content=test_content,
        content_type="gong_call",
        source_id="test_context_call",
        priority="normal"
    )
    
    # Check that context is preserved
    for chunk in chunks:
        metadata = chunk["metadata"]
        assert "conversation_context" in metadata
        assert "full_context_available" in metadata

@pytest.mark.asyncio
async def test_ai_agent_integration(chunking_pipeline):
    """Test AI agent integration"""
    
    test_content = """
    The client is very satisfied with our platform and wants to expand to 1000 units.
    This represents a $50k increase in revenue. We need to prepare a proposal.
    """
    
    chunks = await chunking_pipeline.process_content(
        content=test_content,
        content_type="slack_message",
        source_id="test_ai_message",
        priority="normal"
    )
    
    # Check for AI enhancements
    for chunk in chunks:
        assert "ai_enhancements" in chunk
        assert "automated_actions" in chunk
        assert "slack_notifications" in chunk

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__]) 