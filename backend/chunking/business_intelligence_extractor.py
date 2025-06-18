"""
Sophia AI - Business Intelligence Extractor
Extract comprehensive business intelligence from content chunks
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class BusinessIntelligenceExtractor:
    """Extract comprehensive business intelligence from chunks"""
    
    def __init__(self):
        self.financial_indicators = [
            'revenue', 'budget', 'cost', 'price', 'investment',
            'ROI', 'profit', 'loss', 'savings', 'expense', 'pricing',
            'quote', 'proposal', 'deal', 'contract', 'payment'
        ]
        
        self.technology_indicators = [
            'api', 'integration', 'system', 'platform', 'software',
            'automation', 'workflow', 'database', 'cloud', 'security',
            'implementation', 'setup', 'configuration', 'deployment'
        ]
        
        self.performance_indicators = [
            'performance', 'efficiency', 'productivity', 'speed',
            'accuracy', 'quality', 'satisfaction', 'success', 'metrics',
            'kpi', 'dashboard', 'reporting', 'analytics'
        ]
        
        self.apartment_industry_indicators = {
            'property_management': [
                'maintenance', 'work order', 'tenant', 'resident',
                'lease', 'rent collection', 'vacancy', 'occupancy',
                'property', 'building', 'unit', 'apartment'
            ],
            'financial_operations': [
                'rent roll', 'payment', 'collection', 'budget',
                'revenue', 'expense', 'profit', 'loss', 'financial',
                'accounting', 'billing', 'invoicing'
            ],
            'leasing_operations': [
                'leasing', 'marketing', 'tour', 'application',
                'screening', 'move-in', 'move-out', 'prospect',
                'lead', 'conversion', 'lease-up'
            ],
            'compliance_regulatory': [
                'fair housing', 'compliance', 'regulation',
                'legal', 'policy', 'procedure', 'audit', 'inspection'
            ],
            'technology_integration': [
                'software', 'system', 'integration', 'api',
                'automation', 'workflow', 'process', 'platform'
            ]
        }
        
        logger.info("Business Intelligence Extractor initialized")
    
    async def extract_business_intelligence(
        self, 
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract comprehensive business intelligence"""
        
        enhanced_chunks = []
        
        for chunk in chunks:
            text = chunk.get("text", "")
            
            # Extract financial intelligence
            financial_intel = self._extract_financial_intelligence(text)
            
            # Extract technology intelligence
            tech_intel = self._extract_technology_intelligence(text)
            
            # Extract performance intelligence
            performance_intel = self._extract_performance_intelligence(text)
            
            # Extract apartment industry intelligence
            apartment_intel = self._extract_apartment_industry_intelligence(text)
            
            # Extract decision maker intelligence
            decision_maker_intel = self._extract_decision_maker_intelligence(text)
            
            # Extract action items
            action_items = self._extract_action_items(text)
            
            enhanced_chunk = {
                **chunk,
                "business_intelligence": {
                    "financial": financial_intel,
                    "technology": tech_intel,
                    "performance": performance_intel,
                    "apartment_industry": apartment_intel,
                    "decision_makers": decision_maker_intel,
                    "action_items": action_items
                },
                "revenue_potential": financial_intel.get("revenue_potential", 0),
                "technology_relevance": tech_intel.get("relevance_score", 0),
                "performance_impact": performance_intel.get("impact_score", 0),
                "apartment_industry_relevance": apartment_intel.get("overall_relevance", 0)
            }
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def _extract_financial_intelligence(self, text: str) -> Dict[str, Any]:
        """Extract financial intelligence from text"""
        
        text_lower = text.lower()
        
        # Look for monetary values
        money_pattern = r'\$[\d,]+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*(?:k|K|m|M|million|thousand)'
        monetary_mentions = re.findall(money_pattern, text)
        
        # Convert monetary values to numbers
        monetary_values = []
        for mention in monetary_mentions:
            value = self._parse_monetary_value(mention)
            if value:
                monetary_values.append(value)
        
        # Look for financial context
        financial_context = {
            "revenue_mention": any(word in text_lower for word in ["revenue", "sales", "income"]),
            "cost_mention": any(word in text_lower for word in ["cost", "expense", "budget"]),
            "investment_mention": any(word in text_lower for word in ["investment", "ROI", "return"]),
            "pricing_mention": any(word in text_lower for word in ["pricing", "price", "quote", "proposal"]),
            "monetary_values": monetary_values,
            "revenue_potential": self._estimate_revenue_potential(text, monetary_values),
            "financial_urgency": self._assess_financial_urgency(text_lower)
        }
        
        return financial_context
    
    def _parse_monetary_value(self, mention: str) -> Optional[float]:
        """Parse monetary value from text"""
        
        try:
            # Remove currency symbols and commas
            clean_value = re.sub(r'[$,]', '', mention)
            
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
            return None
    
    def _estimate_revenue_potential(self, text: str, monetary_values: List[float]) -> float:
        """Estimate revenue potential from text and monetary values"""
        
        text_lower = text.lower()
        
        # Base score from monetary values
        base_score = sum(monetary_values) if monetary_values else 0
        
        # Boost for revenue-related keywords
        revenue_boost = 0
        if any(word in text_lower for word in ["revenue", "sales", "deal", "contract"]):
            revenue_boost = base_score * 0.5
        
        # Boost for urgency indicators
        urgency_boost = 0
        if any(word in text_lower for word in ["urgent", "asap", "immediate", "critical"]):
            urgency_boost = base_score * 0.3
        
        return base_score + revenue_boost + urgency_boost
    
    def _assess_financial_urgency(self, text: str) -> str:
        """Assess financial urgency level"""
        
        if any(word in text for word in ["urgent", "asap", "immediate", "critical"]):
            return "high"
        elif any(word in text for word in ["soon", "quickly", "fast", "priority"]):
            return "medium"
        else:
            return "low"
    
    def _extract_technology_intelligence(self, text: str) -> Dict[str, Any]:
        """Extract technology intelligence from text"""
        
        text_lower = text.lower()
        
        tech_keywords = {
            "api_integration": ["api", "integration", "connect", "sync", "webhook"],
            "platform_mentions": ["platform", "system", "software", "tool", "application"],
            "automation": ["automation", "automated", "workflow", "process", "streamline"],
            "security": ["security", "secure", "encryption", "compliance", "audit"],
            "cloud": ["cloud", "saas", "hosted", "online", "web-based"],
            "implementation": ["implementation", "setup", "configuration", "deployment", "installation"]
        }
        
        tech_scores = {}
        total_mentions = 0
        
        for category, keywords in tech_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            tech_scores[category] = score
            total_mentions += score
        
        # Calculate relevance score
        relevance_score = min(total_mentions / 10.0, 1.0) if total_mentions > 0 else 0.0
        
        return {
            "technology_mentions": tech_scores,
            "relevance_score": relevance_score,
            "primary_tech_focus": max(tech_scores, key=tech_scores.get) if tech_scores else None,
            "total_tech_mentions": total_mentions,
            "technology_urgency": self._assess_technology_urgency(text_lower)
        }
    
    def _assess_technology_urgency(self, text: str) -> str:
        """Assess technology urgency level"""
        
        if any(word in text for word in ["urgent", "critical", "broken", "down", "issue"]):
            return "high"
        elif any(word in text for word in ["soon", "needed", "required", "important"]):
            return "medium"
        else:
            return "low"
    
    def _extract_performance_intelligence(self, text: str) -> Dict[str, Any]:
        """Extract performance intelligence from text"""
        
        text_lower = text.lower()
        
        performance_keywords = {
            "metrics": ["metrics", "kpi", "dashboard", "reporting", "analytics"],
            "efficiency": ["efficiency", "productivity", "optimization", "improvement"],
            "quality": ["quality", "accuracy", "reliability", "consistency"],
            "speed": ["speed", "fast", "quick", "performance", "response time"]
        }
        
        performance_scores = {}
        total_mentions = 0
        
        for category, keywords in performance_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            performance_scores[category] = score
            total_mentions += score
        
        # Calculate impact score
        impact_score = min(total_mentions / 8.0, 1.0) if total_mentions > 0 else 0.0
        
        return {
            "performance_mentions": performance_scores,
            "impact_score": impact_score,
            "primary_performance_focus": max(performance_scores, key=performance_scores.get) if performance_scores else None,
            "total_performance_mentions": total_mentions
        }
    
    def _extract_apartment_industry_intelligence(self, text: str) -> Dict[str, Any]:
        """Extract apartment industry-specific intelligence"""
        
        text_lower = text.lower()
        
        industry_scores = {}
        total_relevance = 0
        
        for category, keywords in self.apartment_industry_indicators.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            industry_scores[category] = score
            total_relevance += score
        
        # Calculate overall relevance
        overall_relevance = min(total_relevance / 20.0, 1.0) if total_relevance > 0 else 0.0
        
        return {
            "industry_scores": industry_scores,
            "overall_relevance": overall_relevance,
            "primary_industry_focus": max(industry_scores, key=industry_scores.get) if industry_scores else None,
            "total_industry_mentions": total_relevance
        }
    
    def _extract_decision_maker_intelligence(self, text: str) -> Dict[str, Any]:
        """Extract decision maker intelligence"""
        
        # Look for decision maker indicators
        decision_indicators = [
            "ceo", "cto", "cfo", "vp", "director", "manager",
            "owner", "founder", "president", "head of", "lead"
        ]
        
        decision_makers = []
        for indicator in decision_indicators:
            if indicator in text.lower():
                # Extract the full name/title
                pattern = rf'\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+{indicator}\b'
                matches = re.findall(pattern, text, re.IGNORECASE)
                decision_makers.extend(matches)
        
        # Look for decision-making language
        decision_language = [
            "decide", "decision", "approve", "sign", "authorize",
            "final say", "make the call", "green light"
        ]
        
        has_decision_language = any(phrase in text.lower() for phrase in decision_language)
        
        return {
            "decision_makers": list(set(decision_makers)),
            "decision_maker_count": len(set(decision_makers)),
            "has_decision_maker": len(decision_makers) > 0,
            "has_decision_language": has_decision_language,
            "decision_urgency": "high" if has_decision_language else "low"
        }
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items from text"""
        
        action_items = []
        text_lower = text.lower()
        
        # Action item patterns
        action_patterns = [
            r'(?:need to|will|going to|plan to)\s+([^.!?]+)',
            r'(?:action item|todo|task|follow up)\s*:?\s*([^.!?]+)',
            r'(?:send|email|call|meet|schedule)\s+([^.!?]+)',
            r'(?:prepare|create|update|review)\s+([^.!?]+)'
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                action_item = match.strip()
                if len(action_item) > 5:  # Minimum meaningful length
                    action_items.append(action_item)
        
        return list(set(action_items))  # Remove duplicates 