"""
Sophia AI - Emotional Boundary Chunker
Detect emotional shifts and create emotional context chunks
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class EmotionalBoundaryChunker:
    """Detect emotional shifts and create emotional context chunks"""
    
    def __init__(self):
        self.emotion_indicators = {
            'frustration': ['frustrated', 'annoyed', 'upset', 'angry', 'irritated'],
            'satisfaction': ['happy', 'pleased', 'satisfied', 'excited', 'thrilled'],
            'concern': ['worried', 'concerned', 'nervous', 'anxious', 'uncertain'],
            'confidence': ['confident', 'sure', 'certain', 'positive', 'optimistic'],
            'urgency': ['urgent', 'asap', 'critical', 'emergency', 'immediate']
        }
        
        logger.info("Emotional Boundary Chunker initialized")
    
    async def chunk_by_emotional_shifts(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create chunks around emotional shifts"""
        
        enhanced_chunks = []
        
        for chunk in chunks:
            # Analyze emotional content
            emotion_analysis = self._analyze_emotions(chunk["text"])
            
            if emotion_analysis["primary_emotion"]:
                emotional_chunk = {
                    **chunk,
                    "chunk_type": "emotional_context",
                    "primary_emotion": emotion_analysis["primary_emotion"],
                    "emotion_intensity": emotion_analysis["intensity"],
                    "emotion_shift": emotion_analysis["is_shift"],
                    "requires_attention": emotion_analysis["requires_attention"]
                }
                enhanced_chunks.append(emotional_chunk)
            
            enhanced_chunks.append(chunk)
        
        return enhanced_chunks
    
    def _analyze_emotions(self, text: str) -> Dict[str, Any]:
        """Analyze emotions in text"""
        
        text_lower = text.lower()
        emotion_scores = {}
        
        # Calculate emotion scores
        for emotion, indicators in self.emotion_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            emotion_scores[emotion] = score
        
        # Find primary emotion
        primary_emotion = None
        max_score = 0
        
        for emotion, score in emotion_scores.items():
            if score > max_score:
                max_score = score
                primary_emotion = emotion
        
        # Calculate intensity
        total_emotion_words = sum(emotion_scores.values())
        total_words = len(text.split())
        intensity = total_emotion_words / max(total_words / 10, 1) if total_words > 0 else 0
        
        # Determine if this is an emotional shift
        is_shift = max_score >= 2  # Multiple emotion words indicate shift
        
        # Determine if attention is required
        requires_attention = (
            primary_emotion in ['frustration', 'concern', 'urgency'] or
            intensity > 0.3
        )
        
        return {
            "primary_emotion": primary_emotion,
            "emotion_scores": emotion_scores,
            "intensity": min(intensity, 1.0),
            "is_shift": is_shift,
            "requires_attention": requires_attention
        } 