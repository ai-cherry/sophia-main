"""
Sophia AI - Decision Maker Extractor
Extract decision makers from conversation content
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DecisionMakerExtractor:
    """Extract decision makers from conversation content"""
    
    def __init__(self):
        self.decision_indicators = [
            "ceo", "cto", "cfo", "vp", "director", "manager",
            "owner", "founder", "president", "head of", "lead",
            "chief", "executive", "senior", "principal"
        ]
        
        self.decision_language = [
            "decide", "decision", "approve", "sign", "authorize",
            "final say", "make the call", "green light", "okay",
            "yes", "agree", "proceed", "move forward"
        ]
        
        logger.info("Decision Maker Extractor initialized")
    
    async def extract_decision_makers(self, text: str) -> List[str]:
        """Extract decision makers from text"""
        
        if not text or not text.strip():
            return []
        
        decision_makers = []
        
        # Look for decision maker indicators
        for indicator in self.decision_indicators:
            if indicator in text.lower():
                # Extract the full name/title
                pattern = rf'\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+{indicator}\b'
                matches = re.findall(pattern, text, re.IGNORECASE)
                decision_makers.extend(matches)
        
        # Look for decision-making language with names
        decision_patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:will|can|should)\s+(?:decide|approve|sign)',
            r'(?:decided by|approved by|signed by)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:has|needs)\s+(?:final|ultimate)\s+(?:say|approval)'
        ]
        
        for pattern in decision_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            decision_makers.extend(matches)
        
        # Remove duplicates and clean up
        unique_decision_makers = []
        for dm in decision_makers:
            dm_clean = dm.strip()
            if dm_clean and dm_clean not in unique_decision_makers:
                unique_decision_makers.append(dm_clean)
        
        return unique_decision_makers 