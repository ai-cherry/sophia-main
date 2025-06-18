"""
Sophia AI - Hierarchical Topic Classifier
Hierarchical topic classification with dynamic subcategories
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class HierarchicalTopicClassifier:
    """Hierarchical topic classification with dynamic subcategories"""
    
    def __init__(self):
        self.topic_hierarchy = {
            "sales": {
                "pricing": ["negotiation", "quotes", "proposals", "discounts"],
                "prospecting": ["lead_generation", "qualification", "outreach"],
                "closing": ["contracts", "signatures", "deals", "commitments"],
                "relationship": ["follow_up", "maintenance", "expansion"]
            },
            "technical": {
                "integration": ["api", "webhooks", "data_sync", "automation"],
                "implementation": ["setup", "configuration", "deployment"],
                "support": ["troubleshooting", "maintenance", "updates"],
                "architecture": ["design", "scalability", "security"]
            },
            "financial": {
                "billing": ["invoicing", "payments", "collections"],
                "budgeting": ["planning", "forecasting", "analysis"],
                "reporting": ["metrics", "dashboards", "analytics"],
                "compliance": ["audits", "regulations", "policies"]
            },
            "operations": {
                "process": ["workflows", "efficiency", "optimization"],
                "team": ["collaboration", "communication", "coordination"],
                "quality": ["standards", "monitoring", "improvement"],
                "scaling": ["growth", "expansion", "capacity"]
            }
        }
        
        logger.info("Hierarchical Topic Classifier initialized")
    
    async def classify_topics_hierarchically(
        self, 
        text: str
    ) -> Dict[str, Any]:
        """Classify text using hierarchical topic structure"""
        
        # Use AI to determine primary and secondary topics
        ai_classification = await self._ai_topic_classification(text)
        
        # Map to hierarchical structure
        hierarchical_topics = self._map_to_hierarchy(ai_classification)
        
        # Add confidence scores
        confidence_scores = self._calculate_confidence_scores(hierarchical_topics)
        
        return {
            "primary_topic": hierarchical_topics["primary"],
            "secondary_topics": hierarchical_topics["secondary"],
            "subtopics": hierarchical_topics["subtopics"],
            "confidence_scores": confidence_scores,
            "topic_hierarchy": hierarchical_topics["hierarchy"]
        }
    
    async def _ai_topic_classification(self, text: str) -> Dict[str, Any]:
        """Use AI to classify topics dynamically"""
        
        # This would use OpenAI or similar for dynamic classification
        # For now, use pattern-based classification
        
        text_lower = text.lower()
        
        # Pattern-based classification
        topic_scores = {}
        
        for primary_topic, subtopics in self.topic_hierarchy.items():
            score = 0
            for subtopic, keywords in subtopics.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        score += 1
            topic_scores[primary_topic] = score
        
        # Get the highest scoring topic
        if topic_scores:
            primary_topic = max(topic_scores, key=topic_scores.get)
            confidence = min(topic_scores[primary_topic] / 5.0, 1.0)  # Normalize confidence
        else:
            primary_topic = "general"
            confidence = 0.5
        
        # Find specific subtopics
        subtopics = []
        for subtopic, keywords in self.topic_hierarchy.get(primary_topic, {}).items():
            for keyword in keywords:
                if keyword in text_lower:
                    subtopics.append(subtopic)
                    break
        
        return {
            "primary_topic": primary_topic,
            "secondary_topics": [],  # Would be populated by AI
            "specific_subtopics": subtopics,
            "confidence_score": confidence
        }
    
    def _map_to_hierarchy(self, ai_classification: Dict[str, Any]) -> Dict[str, Any]:
        """Map AI classification to hierarchical structure"""
        
        primary_topic = ai_classification.get("primary_topic", "general")
        subtopics = ai_classification.get("specific_subtopics", [])
        
        # Get the hierarchy for the primary topic
        hierarchy = self.topic_hierarchy.get(primary_topic, {})
        
        return {
            "primary": primary_topic,
            "secondary": ai_classification.get("secondary_topics", []),
            "subtopics": subtopics,
            "hierarchy": hierarchy
        }
    
    def _calculate_confidence_scores(self, hierarchical_topics: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence scores for the classification"""
        
        primary_topic = hierarchical_topics["primary"]
        subtopics = hierarchical_topics["subtopics"]
        
        # Base confidence on primary topic
        base_confidence = 0.8 if primary_topic != "general" else 0.5
        
        # Boost confidence if subtopics are found
        subtopic_boost = min(len(subtopics) * 0.1, 0.2)
        
        return {
            "overall": min(base_confidence + subtopic_boost, 1.0),
            "primary_topic": base_confidence,
            "subtopics": subtopic_boost
        } 