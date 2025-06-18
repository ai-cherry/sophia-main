"""
Sophia AI - Decision Point Chunker
Detect and chunk around business decision points
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DecisionPointChunker:
    """Detect and chunk around business decision points"""
    
    def __init__(self):
        self.decision_indicators = {
            'explicit_decisions': [
                'we\'ll go with', 'we\'ve decided', 'let\'s proceed',
                'I approve', 'we\'re moving forward', 'deal is done',
                'yes, we\'ll do it', 'that works for us', 'we agree'
            ],
            'implicit_decisions': [
                'sounds good', 'that works', 'I agree', 'perfect',
                'let\'s do it', 'I\'m in', 'count me in', 'go ahead'
            ],
            'decision_contexts': [
                'pricing', 'timeline', 'scope', 'features',
                'implementation', 'contract', 'partnership'
            ]
        }
        
        logger.info("Decision Point Chunker initialized")
    
    async def chunk_around_decisions(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify and enhance chunks around decision points"""
        
        enhanced_chunks = []
        
        for chunk in chunks:
            # Check if this chunk contains a decision
            decision_info = self._detect_decision(chunk["text"])
            
            if decision_info["is_decision"]:
                # Create decision-focused chunk
                decision_chunk = {
                    **chunk,
                    "chunk_type": "decision_point",
                    "decision_type": decision_info["type"],
                    "decision_context": decision_info["context"],
                    "decision_confidence": decision_info["confidence"],
                    "requires_follow_up": decision_info["requires_follow_up"],
                    "decision_value": decision_info["estimated_value"]
                }
                enhanced_chunks.append(decision_chunk)
            
            # Also keep original chunk for context
            enhanced_chunks.append(chunk)
        
        return enhanced_chunks
    
    def _detect_decision(self, text: str) -> Dict[str, Any]:
        """Detect decision in text"""
        
        text_lower = text.lower()
        
        # Check for explicit decisions
        for indicator in self.decision_indicators['explicit_decisions']:
            if indicator in text_lower:
                return {
                    "is_decision": True,
                    "type": "explicit",
                    "context": self._identify_decision_context(text_lower),
                    "confidence": 0.9,
                    "requires_follow_up": True,
                    "estimated_value": self._estimate_decision_value(text_lower)
                }
        
        # Check for implicit decisions
        for indicator in self.decision_indicators['implicit_decisions']:
            if indicator in text_lower:
                return {
                    "is_decision": True,
                    "type": "implicit",
                    "context": self._identify_decision_context(text_lower),
                    "confidence": 0.7,
                    "requires_follow_up": True,
                    "estimated_value": self._estimate_decision_value(text_lower)
                }
        
        return {
            "is_decision": False,
            "type": None,
            "context": None,
            "confidence": 0.0,
            "requires_follow_up": False,
            "estimated_value": 0.0
        }
    
    def _identify_decision_context(self, text: str) -> str:
        """Identify the context of the decision"""
        
        for context in self.decision_indicators['decision_contexts']:
            if context in text:
                return context
        
        return "general"
    
    def _estimate_decision_value(self, text: str) -> float:
        """Estimate the value of the decision"""
        
        # Look for monetary values
        money_pattern = r'\$[\d,]+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*(?:k|K|m|M|million|thousand)'
        monetary_mentions = re.findall(money_pattern, text)
        
        if monetary_mentions:
            # Parse the first monetary value
            try:
                value_str = monetary_mentions[0]
                # Remove currency symbols and commas
                clean_value = re.sub(r'[$,]', '', value_str)
                
                # Handle k/K (thousands)
                if 'k' in clean_value.lower():
                    value = float(re.sub(r'[kK]', '', clean_value)) * 1000
                # Handle m/M (millions)
                elif 'm' in clean_value.lower():
                    value = float(re.sub(r'[mM]', '', clean_value)) * 1000000
                # Handle "million"
                elif 'million' in clean_value.lower():
                    value = float(re.sub(r'million', '', clean_value, flags=re.IGNORECASE)) * 1000000
                # Handle "thousand"
                elif 'thousand' in clean_value.lower():
                    value = float(re.sub(r'thousand', '', clean_value, flags=re.IGNORECASE)) * 1000
                else:
                    value = float(clean_value)
                
                return value
            except (ValueError, TypeError):
                pass
        
        # Default value based on decision type
        if any(word in text for word in ["contract", "deal", "partnership"]):
            return 50000  # Default high-value decision
        elif any(word in text for word in ["pricing", "implementation"]):
            return 25000  # Default medium-value decision
        else:
            return 5000   # Default low-value decision 