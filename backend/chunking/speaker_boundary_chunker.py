"""
Sophia AI - Speaker Boundary Chunker
Advanced speaker boundary detection with context preservation
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SpeakerBoundaryChunker:
    """Advanced speaker boundary detection with context preservation"""
    
    def __init__(self):
        self.speaker_patterns = [
            r'^([^:]+):\s*(.+)$',  # Standard speaker format
            r'^([A-Z][a-z]+ [A-Z][a-z]+):\s*(.+)$',  # Full names
            r'^([A-Z]+):\s*(.+)$',  # Abbreviated names
            r'^([A-Z][a-z]+):\s*(.+)$',  # First names
        ]
        
        self.context_window = 3  # Lines of context to preserve
        self.min_chunk_length = 10  # Minimum characters for a chunk
        
        logger.info("Speaker Boundary Chunker initialized")
    
    async def chunk_by_speaker_boundaries(
        self, 
        transcript: str,
        preserve_context: bool = True
    ) -> List[Dict[str, Any]]:
        """Chunk by speaker boundaries while preserving context"""
        
        if not transcript or not transcript.strip():
            return []
        
        chunks = []
        lines = transcript.split('\n')
        current_chunk = {
            "speaker": None,
            "text": "",
            "context_before": [],
            "context_after": [],
            "speaker_metadata": {},
            "chunk_type": "speaker_boundary"
        }
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            speaker_match = self._match_speaker(line)
            
            if speaker_match:
                # Save previous chunk if exists and has content
                if (current_chunk["speaker"] and 
                    current_chunk["text"] and 
                    len(current_chunk["text"]) >= self.min_chunk_length):
                    chunks.append(current_chunk)
                
                # Start new chunk
                current_chunk = {
                    "speaker": speaker_match["speaker"],
                    "text": speaker_match["content"],
                    "context_before": self._get_context_before(lines, i),
                    "context_after": self._get_context_after(lines, i),
                    "speaker_metadata": self._extract_speaker_metadata(speaker_match["speaker"]),
                    "chunk_type": "speaker_boundary"
                }
            else:
                # Continue current chunk
                if current_chunk["speaker"]:
                    current_chunk["text"] += "\n" + line
        
        # Add final chunk if it has content
        if (current_chunk["speaker"] and 
            current_chunk["text"] and 
            len(current_chunk["text"]) >= self.min_chunk_length):
            chunks.append(current_chunk)
        
        logger.info(f"Created {len(chunks)} speaker-based chunks")
        return chunks
    
    def _match_speaker(self, line: str) -> Optional[Dict[str, str]]:
        """Match speaker pattern in a line"""
        
        for pattern in self.speaker_patterns:
            match = re.match(pattern, line)
            if match:
                speaker = match.group(1).strip()
                content = match.group(2).strip() if len(match.groups()) > 1 else ""
                
                # Validate speaker name
                if self._is_valid_speaker(speaker):
                    return {
                        "speaker": speaker,
                        "content": content
                    }
        
        return None
    
    def _is_valid_speaker(self, speaker: str) -> bool:
        """Validate if a speaker name is reasonable"""
        
        if not speaker or len(speaker) < 2:
            return False
        
        # Check for common non-speaker patterns
        non_speaker_patterns = [
            r'^\d+$',  # Just numbers
            r'^[A-Z]{1,2}$',  # Very short abbreviations
            r'^[^a-zA-Z]+$',  # No letters
        ]
        
        for pattern in non_speaker_patterns:
            if re.match(pattern, speaker):
                return False
        
        return True
    
    def _get_context_before(self, lines: List[str], current_index: int) -> List[str]:
        """Get context lines before current position"""
        
        start_index = max(0, current_index - self.context_window)
        context_lines = []
        
        for i in range(start_index, current_index):
            if i < len(lines) and lines[i].strip():
                context_lines.append(lines[i].strip())
        
        return context_lines
    
    def _get_context_after(self, lines: List[str], current_index: int) -> List[str]:
        """Get context lines after current position"""
        
        end_index = min(len(lines), current_index + self.context_window + 1)
        context_lines = []
        
        for i in range(current_index + 1, end_index):
            if i < len(lines) and lines[i].strip():
                context_lines.append(lines[i].strip())
        
        return context_lines
    
    def _extract_speaker_metadata(self, speaker: str) -> Dict[str, Any]:
        """Extract metadata about the speaker"""
        
        metadata = {
            "name": speaker,
            "name_type": self._classify_name_type(speaker),
            "is_internal": self._is_internal_speaker(speaker),
            "role": self._extract_role(speaker),
            "company": self._extract_company(speaker)
        }
        
        return metadata
    
    def _classify_name_type(self, speaker: str) -> str:
        """Classify the type of speaker name"""
        
        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', speaker):
            return "full_name"
        elif re.match(r'^[A-Z]+$', speaker):
            return "abbreviation"
        elif re.match(r'^[A-Z][a-z]+$', speaker):
            return "first_name"
        else:
            return "other"
    
    def _is_internal_speaker(self, speaker: str) -> bool:
        """Determine if speaker is internal to the company"""
        
        # Common internal speaker patterns
        internal_indicators = [
            "sales", "account", "customer", "support", "success",
            "marketing", "product", "engineering", "operations"
        ]
        
        speaker_lower = speaker.lower()
        return any(indicator in speaker_lower for indicator in internal_indicators)
    
    def _extract_role(self, speaker: str) -> Optional[str]:
        """Extract role from speaker name"""
        
        # Look for role indicators in speaker name
        role_patterns = {
            "sales": ["sales", "account", "rep"],
            "support": ["support", "help", "service"],
            "management": ["manager", "director", "vp", "ceo", "cto"],
            "technical": ["engineer", "developer", "architect", "technical"]
        }
        
        speaker_lower = speaker.lower()
        for role, indicators in role_patterns.items():
            if any(indicator in speaker_lower for indicator in indicators):
                return role
        
        return None
    
    def _extract_company(self, speaker: str) -> Optional[str]:
        """Extract company name from speaker"""
        
        # Look for company indicators
        company_patterns = [
            r'\(([^)]+)\)',  # Text in parentheses
            r'\[([^\]]+)\]',  # Text in brackets
            r'from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "from Company"
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, speaker, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None 