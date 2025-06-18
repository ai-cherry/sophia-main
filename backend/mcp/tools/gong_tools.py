import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

from ..sophia_mcp_server import MCPTool
from ...integrations.gong.enhanced_gong_integration import GongClient

class GongCallAnalysisTool(MCPTool):
    """Tool for analyzing Gong call recordings"""
    
    def __init__(self):
        super().__init__(
            name="gong_call_analysis",
            description="Analyze a Gong call recording to extract insights and recommendations",
            parameters={
                "call_id": {
                    "type": "string",
                    "description": "ID of the Gong call to analyze",
                    "required": True
                },
                "analysis_type": {
                    "type": "string",
                    "description": "Type of analysis to perform",
                    "enum": ["basic", "detailed", "coaching", "sentiment"],
                    "required": False,
                    "default": "detailed"
                },
                "include_transcript": {
                    "type": "boolean",
                    "description": "Whether to include the transcript in the response",
                    "required": False,
                    "default": False
                }
            }
        )
        self.logger = logging.getLogger(__name__)
        self.gong_client = None
        
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the provided parameters"""
        # Get parameters
        call_id = parameters["call_id"]
        analysis_type = parameters.get("analysis_type", "detailed")
        include_transcript = parameters.get("include_transcript", False)
        
        # Initialize Gong client if not already initialized
        if not self.gong_client:
            self.gong_client = GongClient()
            await self.gong_client.setup()
        
        try:
            # Get call details
            call_detail = await self.gong_client.get_call_detail(call_id)
            
            # Extract transcript if needed
            transcript_text = ""
            if include_transcript or analysis_type in ["detailed", "coaching", "sentiment"]:
                if "transcript" in call_detail:
                    transcript_text = await self.gong_client.extract_transcript_text(call_detail["transcript"])
            
            # Perform analysis based on type
            if analysis_type == "basic":
                analysis = await self._perform_basic_analysis(call_detail)
            elif analysis_type == "detailed":
                analysis = await self._perform_detailed_analysis(call_detail, transcript_text)
            elif analysis_type == "coaching":
                analysis = await self._perform_coaching_analysis(call_detail, transcript_text)
            elif analysis_type == "sentiment":
                analysis = await self._perform_sentiment_analysis(call_detail, transcript_text)
            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")
            
            # Prepare response
            response = {
                "call_id": call_id,
                "analysis_type": analysis_type,
                "analysis": analysis,
                "metadata": {
                    "call_date": call_detail.get("dateTime"),
                    "duration_seconds": call_detail.get("durationSeconds"),
                    "participants": [
                        {
                            "name": p.get("name"),
                            "email": p.get("email"),
                            "role": p.get("role"),
                            "company": p.get("company")
                        }
                        for p in call_detail.get("participants", [])
                    ]
                }
            }
            
            # Include transcript if requested
            if include_transcript:
                response["transcript"] = transcript_text
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error analyzing call: {e}")
            return {
                "error": str(e),
                "call_id": call_id
            }
    
    async def _perform_basic_analysis(self, call_detail: Dict[str, Any]) -> Dict[str, Any]:
        """Perform basic analysis of a call"""
        # Extract basic information
        call_date = call_detail.get("dateTime")
        duration_seconds = call_detail.get("durationSeconds")
        direction = call_detail.get("direction")
        
        # Extract participants
        participants = call_detail.get("participants", [])
        customer_participants = [p for p in participants if p.get("isFromCustomer", False)]
        internal_participants = [p for p in participants if not p.get("isFromCustomer", False)]
        
        # Extract topics
        topics = call_detail.get("topics", [])
        
        # Create basic analysis
        analysis = {
            "summary": {
                "call_date": call_date,
                "duration_minutes": round(duration_seconds / 60, 1) if duration_seconds else None,
                "direction": direction,
                "customer_count": len(customer_participants),
                "internal_count": len(internal_participants),
                "topic_count": len(topics)
            },
            "participants": {
                "customers": [
                    {
                        "name": p.get("name"),
                        "company": p.get("company")
                    }
                    for p in customer_participants
                ],
                "internal": [
                    {
                        "name": p.get("name"),
                        "role": p.get("role")
                    }
                    for p in internal_participants
                ]
            },
            "topics": [
                {
                    "name": topic.get("name"),
                    "score": topic.get("score")
                }
                for topic in topics
            ]
        }
        
        return analysis
    
    async def _perform_detailed_analysis(self, call_detail: Dict[str, Any], transcript_text: str) -> Dict[str, Any]:
        """Perform detailed analysis of a call"""
        # Get basic analysis
        basic_analysis = await self._perform_basic_analysis(call_detail)
        
        # Extract additional information
        trackers = call_detail.get("trackers", [])
        stats = call_detail.get("stats", {})
        
        # Analyze transcript
        transcript_analysis = await self._analyze_transcript(transcript_text)
        
        # Create detailed analysis
        analysis = {
            **basic_analysis,
            "trackers": [
                {
                    "name": tracker.get("name"),
                    "count": tracker.get("count"),
                    "type": tracker.get("type")
                }
                for tracker in trackers
            ],
            "stats": {
                "talk_ratio": stats.get("talkRatio", {}).get("value"),
                "longest_monologue": stats.get("longestMonologue", {}).get("value"),
                "interactivity": stats.get("interactivity", {}).get("value"),
                "patience": stats.get("patience", {}).get("value")
            },
            "transcript_analysis": transcript_analysis
        }
        
        return analysis
    
    async def _perform_coaching_analysis(self, call_detail: Dict[str, Any], transcript_text: str) -> Dict[str, Any]:
        """Perform coaching analysis of a call"""
        # Get detailed analysis
        detailed_analysis = await self._perform_detailed_analysis(call_detail, transcript_text)
        
        # Extract coaching information
        trackers = call_detail.get("trackers", [])
        stats = call_detail.get("stats", {})
        
        # Identify strengths and areas for improvement
        strengths = []
        improvements = []
        
        # Analyze talk ratio
        talk_ratio = stats.get("talkRatio", {}).get("value")
        if talk_ratio is not None:
            if talk_ratio < 0.35:
                strengths.append("Good listening skills - allowed customer to speak")
            elif talk_ratio > 0.65:
                improvements.append("Consider talking less and listening more to the customer")
        
        # Analyze interactivity
        interactivity = stats.get("interactivity", {}).get("value")
        if interactivity is not None:
            if interactivity > 3:
                strengths.append("Good back-and-forth conversation")
            elif interactivity < 2:
                improvements.append("Work on creating more interactive conversations")
        
        # Analyze patience
        patience = stats.get("patience", {}).get("value")
        if patience is not None:
            if patience > 1.5:
                strengths.append("Good patience in responses")
            elif patience < 0.8:
                improvements.append("Consider pausing more before responding")
        
        # Analyze trackers
        discovery_questions = 0
        for tracker in trackers:
            if "discovery question" in tracker.get("name", "").lower():
                discovery_questions += tracker.get("count", 0)
        
        if discovery_questions >= 3:
            strengths.append(f"Asked {discovery_questions} discovery questions")
        elif discovery_questions < 2:
            improvements.append("Ask more discovery questions")
        
        # Create coaching analysis
        coaching_analysis = {
            "strengths": strengths,
            "areas_for_improvement": improvements,
            "recommendations": [
                "Review call recording to identify specific moments for improvement",
                "Practice active listening techniques",
                "Prepare discovery questions before calls"
            ]
        }
        
        # Combine with detailed analysis
        analysis = {
            **detailed_analysis,
            "coaching": coaching_analysis
        }
        
        return analysis
    
    async def _perform_sentiment_analysis(self, call_detail: Dict[str, Any], transcript_text: str) -> Dict[str, Any]:
        """Perform sentiment analysis of a call"""
        # Get basic analysis
        basic_analysis = await self._perform_basic_analysis(call_detail)
        
        # Analyze transcript for sentiment
        if not transcript_text:
            return {
                **basic_analysis,
                "sentiment": {
                    "error": "No transcript available for sentiment analysis"
                }
            }
        
        # Split transcript by speaker
        speaker_segments = {}
        current_speaker = None
        
        for line in transcript_text.split("\n"):
            speaker_match = re.match(r"^([^:]+):", line)
            if speaker_match:
                current_speaker = speaker_match.group(1).strip()
                if current_speaker not in speaker_segments:
                    speaker_segments[current_speaker] = []
                content = line[len(current_speaker) + 1:].strip()
                if content:
                    speaker_segments[current_speaker].append(content)
            elif current_speaker and line.strip():
                speaker_segments[current_speaker].append(line.strip())
        
        # Analyze sentiment for each speaker
        sentiment_by_speaker = {}
        overall_sentiment = "neutral"
        
        for speaker, segments in speaker_segments.items():
            # Simple sentiment analysis based on keywords
            positive_words = ["great", "good", "excellent", "happy", "pleased", "thank", "appreciate", "yes", "agree"]
            negative_words = ["bad", "issue", "problem", "concerned", "worried", "no", "not", "don't", "cannot", "won't"]
            
            positive_count = 0
            negative_count = 0
            
            for segment in segments:
                for word in positive_words:
                    positive_count += segment.lower().count(word)
                for word in negative_words:
                    negative_count += segment.lower().count(word)
            
            # Determine sentiment
            if positive_count > negative_count * 1.5:
                speaker_sentiment = "positive"
            elif negative_count > positive_count * 1.5:
                speaker_sentiment = "negative"
            else:
                speaker_sentiment = "neutral"
            
            sentiment_by_speaker[speaker] = {
                "sentiment": speaker_sentiment,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "segment_count": len(segments)
            }
        
        # Determine overall sentiment
        total_positive = sum(s["positive_count"] for s in sentiment_by_speaker.values())
        total_negative = sum(s["negative_count"] for s in sentiment_by_speaker.values())
        
        if total_positive > total_negative * 1.5:
            overall_sentiment = "positive"
        elif total_negative > total_positive * 1.5:
            overall_sentiment = "negative"
        
        # Create sentiment analysis
        sentiment_analysis = {
            "overall_sentiment": overall_sentiment,
            "by_speaker": sentiment_by_speaker,
            "summary": {
                "positive_count": total_positive,
                "negative_count": total_negative
            }
        }
        
        # Combine with basic analysis
        analysis = {
            **basic_analysis,
            "sentiment": sentiment_analysis
        }
        
        return analysis
    
    async def _analyze_transcript(self, transcript_text: str) -> Dict[str, Any]:
        """Analyze transcript text"""
        if not transcript_text:
            return {
                "error": "No transcript available for analysis"
            }
        
        # Split transcript by speaker
        speaker_segments = {}
        current_speaker = None
        
        for line in transcript_text.split("\n"):
            speaker_match = re.match(r"^([^:]+):", line)
            if speaker_match:
                current_speaker = speaker_match.group(1).strip()
                if current_speaker not in speaker_segments:
                    speaker_segments[current_speaker] = []
                content = line[len(current_speaker) + 1:].strip()
                if content:
                    speaker_segments[current_speaker].append(content)
            elif current_speaker and line.strip():
                speaker_segments[current_speaker].append(line.strip())
        
        # Calculate basic metrics
        word_count_by_speaker = {}
        question_count_by_speaker = {}
        
        for speaker, segments in speaker_segments.items():
            word_count = sum(len(segment.split()) for segment in segments)
            word_count_by_speaker[speaker] = word_count
            
            question_count = sum(segment.count("?") for segment in segments)
            question_count_by_speaker[speaker] = question_count
        
        total_words = sum(word_count_by_speaker.values())
        
        # Calculate talk ratio by speaker
        talk_ratio_by_speaker = {
            speaker: count / total_words if total_words > 0 else 0
            for speaker, count in word_count_by_speaker.items()
        }
        
        # Create transcript analysis
        analysis = {
            "speaker_count": len(speaker_segments),
            "total_words": total_words,
            "by_speaker": {
                speaker: {
                    "segment_count": len(segments),
                    "word_count": word_count_by_speaker.get(speaker, 0),
                    "talk_ratio": talk_ratio_by_speaker.get(speaker, 0),
                    "question_count": question_count_by_speaker.get(speaker, 0)
                }
                for speaker, segments in speaker_segments.items()
            }
        }
        
        return analysis

class GongTranscriptExtractionTool(MCPTool):
    """Tool for extracting and processing Gong call transcripts"""
    
    def __init__(self):
        super().__init__(
            name="gong_transcript_extraction",
            description="Extract and process transcripts from Gong call recordings",
            parameters={
                "call_id": {
                    "type": "string",
                    "description": "ID of the Gong call to extract transcript from",
                    "required": True
                },
                "format": {
                    "type": "string",
                    "description": "Format of the extracted transcript",
                    "enum": ["raw", "clean", "structured", "summary"],
                    "required": False,
                    "default": "clean"
                },
                "include_metadata": {
                    "type": "boolean",
                    "description": "Whether to include call metadata in the response",
                    "required": False,
                    "default": True
                }
            }
        )
        self.logger = logging.getLogger(__name__)
        self.gong_client = None
        
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the provided parameters"""
        # Get parameters
        call_id = parameters["call_id"]
        format_type = parameters.get("format", "clean")
        include_metadata = parameters.get("include_metadata", True)
        
        # Initialize Gong client if not already initialized
        if not self.gong_client:
            self.gong_client = GongClient()
            await self.gong_client.setup()
        
        try:
            # Get call details
            call_detail = await self.gong_client.get_call_detail(call_id)
            
            # Extract transcript
            if "transcript" not in call_detail:
                return {
                    "error": "No transcript available for this call",
                    "call_id": call_id
                }
            
            transcript_raw = call_detail["transcript"]
            
            # Process transcript based on format
            if format_type == "raw":
                transcript = transcript_raw
            elif format_type == "clean":
                transcript = await self.gong_client.extract_transcript_text(transcript_raw)
            elif format_type == "structured":
                transcript = await self._extract_structured_transcript(transcript_raw)
            elif format_type == "summary":
                transcript_text = await self.gong_client.extract_transcript_text(transcript_raw)
                transcript = await self._generate_transcript_summary(transcript_text)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
            
            # Prepare response
            response = {
                "call_id": call_id,
                "format": format_type,
                "transcript": transcript
            }
            
            # Include metadata if requested
            if include_metadata:
                response["metadata"] = {
                    "call_date": call_detail.get("dateTime"),
                    "duration_seconds": call_detail.get("durationSeconds"),
                    "participants": [
                        {
                            "name": p.get("name"),
                            "email": p.get("email"),
                            "role": p.get("role"),
                            "company": p.get("company")
                        }
                        for p in call_detail.get("participants", [])
                    ]
                }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error extracting transcript: {e}")
            return {
                "error": str(e),
                "call_id": call_id
            }
    
    async def _extract_structured_transcript(self, transcript_raw: Any) -> List[Dict[str, Any]]:
        """Extract structured transcript from raw transcript"""
        structured_transcript = []
        
        # Process transcript based on its structure
        if isinstance(transcript_raw, list):
            for segment in transcript_raw:
                if isinstance(segment, dict):
                    structured_segment = {
                        "speaker": segment.get("speaker", {}).get("name", "Unknown"),
                        "text": segment.get("text", ""),
                        "start_time": segment.get("startTime"),
                        "end_time": segment.get("endTime")
                    }
                    structured_transcript.append(structured_segment)
        
        return structured_transcript
    
    async def _generate_transcript_summary(self, transcript_text: str) -> Dict[str, Any]:
        """Generate a summary of the transcript"""
        if not transcript_text:
            return {
                "error": "No transcript text available for summarization"
            }
        
        # Split transcript by speaker
        speaker_segments = {}
        current_speaker = None
        
        for line in transcript_text.split("\n"):
            speaker_match = re.match(r"^([^:]+):", line)
            if speaker_match:
                current_speaker = speaker_match.group(1).strip()
                if current_speaker not in speaker_segments:
                    speaker_segments[current_speaker] = []
                content = line[len(current_speaker) + 1:].strip()
                if content:
                    speaker_segments[current_speaker].append(content)
            elif current_speaker and line.strip():
                speaker_segments[current_speaker].append(line.strip())
        
        # Generate simple summary
        summary = {
            "speaker_count": len(speaker_segments),
            "total_lines": sum(len(segments) for segments in speaker_segments.values()),
            "speakers": list(speaker_segments.keys()),
            "key_segments": []
        }
        
        # Extract key segments (simple approach - first and last segment for each speaker)
        for speaker, segments in speaker_segments.items():
            if segments:
                # Add first segment
                summary["key_segments"].append({
                    "speaker": speaker,
                    "text": segments[0],
                    "position": "first"
                })
                
                # Add last segment if different from first
                if len(segments) > 1 and segments[-1] != segments[0]:
                    summary["key_segments"].append({
                        "speaker": speaker,
                        "text": segments[-1],
                        "position": "last"
                    })
        
        return summary
