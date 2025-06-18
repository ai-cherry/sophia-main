"""
Sophia AI - Sentiment Analyzer
Analyze sentiment and emotional context of text
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Analyze sentiment and emotional context of text"""
    
    def __init__(self):
        self.positive_words = [
            "great", "good", "excellent", "happy", "pleased", "thank", 
            "appreciate", "yes", "agree", "perfect", "amazing", "wonderful",
            "satisfied", "excited", "thrilled", "confident", "optimistic"
        ]
        
        self.negative_words = [
            "bad", "issue", "problem", "concerned", "worried", "no", 
            "not", "don't", "cannot", "won't", "frustrated", "angry",
            "disappointed", "upset", "annoyed", "nervous", "anxious"
        ]
        
        self.neutral_words = [
            "okay", "fine", "alright", "maybe", "possibly", "perhaps",
            "neutral", "standard", "normal", "typical", "usual"
        ]
        
        logger.info("Sentiment Analyzer initialized")
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        
        if not text or not text.strip():
            return {
                "score": 0.0,
                "sentiment": "neutral",
                "primary_emotion": None,
                "intensity": 0.0,
                "confidence": 0.0
            }
        
        text_lower = text.lower()
        
        # Count sentiment words
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        neutral_count = sum(1 for word in self.neutral_words if word in text_lower)
        
        # Calculate sentiment score (-1 to 1)
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            score = 0.0
        else:
            score = (positive_count - negative_count) / total_sentiment_words
        
        # Determine sentiment category
        if score > 0.2:
            sentiment = "positive"
        elif score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Calculate intensity
        intensity = min(total_sentiment_words / max(len(text.split()) / 10, 1), 1.0)
        
        # Determine primary emotion
        primary_emotion = self._determine_primary_emotion(text_lower)
        
        # Calculate confidence
        confidence = min(total_sentiment_words / 5.0, 1.0)
        
        return {
            "score": score,
            "sentiment": sentiment,
            "primary_emotion": primary_emotion,
            "intensity": intensity,
            "confidence": confidence,
            "word_counts": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            }
        }
    
    def _determine_primary_emotion(self, text: str) -> Optional[str]:
        """Determine the primary emotion in the text"""
        
        emotion_indicators = {
            "frustration": ["frustrated", "annoyed", "irritated", "upset"],
            "satisfaction": ["satisfied", "pleased", "happy", "content"],
            "concern": ["concerned", "worried", "nervous", "anxious"],
            "confidence": ["confident", "sure", "certain", "positive"],
            "urgency": ["urgent", "asap", "critical", "emergency"],
            "excitement": ["excited", "thrilled", "amazed", "wonderful"]
        }
        
        emotion_scores = {}
        for emotion, indicators in emotion_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text)
            emotion_scores[emotion] = score
        
        # Find emotion with highest score
        if emotion_scores:
            max_score = max(emotion_scores.values())
            if max_score > 0:
                for emotion, score in emotion_scores.items():
                    if score == max_score:
                        return emotion
        
        return None 