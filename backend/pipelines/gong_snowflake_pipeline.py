import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import snowflake.connector
import pinecone
from ..integrations.gong.enhanced_gong_integration import EnhancedGongIntegration
from ..core.secret_manager import secret_manager

class GongSnowflakePipeline:
    """Pipeline for Gong → Snowflake → Vector DB"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gong_client = None
        self.sf_conn = None
        self.pinecone_index = None
        self.openai_client = None
        
    async def setup_connections(self):
        """Initialize all connections"""
        # Gong connection
        self.gong_client = EnhancedGongIntegration()
        await self.gong_client.setup()
        
        # Snowflake connection
        sf_config = {
            "account": await secret_manager.get_secret("account", "snowflake"),
            "user": await secret_manager.get_secret("user", "snowflake"),
            "password": await secret_manager.get_secret("password", "snowflake"),
            "warehouse": "COMPUTE_WH",
            "database": "SOPHIA_DB",
            "schema": "RAW_DATA"
        }
        self.sf_conn = snowflake.connector.connect(**sf_config)
        
        # Pinecone connection
        pinecone_key = await secret_manager.get_secret("api_key", "pinecone")
        pinecone.init(api_key=pinecone_key, environment="us-east1-gcp")
        self.pinecone_index = pinecone.Index("sophia-interactions")
        
        # OpenAI for embeddings
        try:
            from openai import OpenAI
            openai_key = await secret_manager.get_secret("api_key", "openai")
            self.openai_client = OpenAI(api_key=openai_key)
        except ImportError:
            self.logger.warning("OpenAI package not installed. Vector embeddings will not be available.")
        
    async def run_daily_sync(self):
        """Daily sync of all Gong data (calls + emails + meetings)"""
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")
        
        # 1. Extract from Gong (all conversation types)
        conversations = await self.gong_client.get_conversations_by_date_range(
            start_date=f"{date_str}T00:00:00Z",
            end_date=f"{date_str}T23:59:59Z"
        )
        
        self.logger.info(f"Extracted {len(conversations)} conversations from Gong")
        
        # 2. Load to Snowflake (normalized structure)
        await self._load_conversations_to_snowflake(conversations)
        
        # 3. Generate embeddings and load to Pinecone
        if self.openai_client:
            await self._embed_and_store_conversations(conversations)
        
    async def _load_conversations_to_snowflake(self, conversations: List[Dict[str, Any]]):
        """Load conversations to Snowflake with proper normalization"""
        cursor = self.sf_conn.cursor()
        
        for conv in conversations:
            try:
                conv_type = conv["conversation_type"]
                
                # 1. Insert into CONVERSATIONS table
                cursor.execute("""
                    INSERT INTO GONG_CONVERSATIONS 
                    (conversation_id, conversation_key, conversation_type, 
                     conversation_datetime, workspace_ids, is_deleted)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (conversation_key) DO UPDATE SET
                    etl_modified_datetime = CURRENT_TIMESTAMP()
                """, (
                    conv["id"],
                    conv.get("conversationKey", f"{conv_type}_{conv['id']}"),
                    conv_type,
                    conv.get("dateTime"),
                    json.dumps(conv.get("workspaceIds", [])),
                    conv.get("isDeleted", False)
                ))
                
                # 2. Insert type-specific data
                if conv_type == "call":
                    await self._insert_call_data(cursor, conv)
                elif conv_type == "email":
                    await self._insert_email_data(cursor, conv)
                
                # 3. Insert participants
                await self._insert_participants(cursor, conv)
                
                # 4. Insert trackers (topics/keywords)
                await self._insert_trackers(cursor, conv)
                
                # 5. Insert CRM context
                await self._insert_crm_context(cursor, conv)
                
            except Exception as e:
                self.logger.error(f"Failed to load conversation {conv['id']}: {e}")
                
        cursor.close()
        
    async def _insert_call_data(self, cursor, call_data: Dict[str, Any]):
        """Insert call-specific data"""
        conversation_key = call_data.get("conversationKey", f"call_{call_data['id']}")
        
        cursor.execute("""
            INSERT INTO GONG_CALLS 
            (conversation_key, conversation_id, call_url, direction, disposition,
             duration_seconds, effective_start_datetime, planned_start_datetime,
             planned_end_datetime, scope, owner_id, phone_number,
             call_spotlight_brief, call_spotlight_key_points, 
             call_spotlight_next_steps, call_spotlight_outcome,
             call_spotlight_type, question_company_count, 
             question_non_company_count, presentation_duration_sec,
             browser_duration_sec, webcam_non_company_duration_sec)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (conversation_key) DO UPDATE SET
            call_spotlight_brief = EXCLUDED.call_spotlight_brief,
            call_spotlight_key_points = EXCLUDED.call_spotlight_key_points,
            call_spotlight_next_steps = EXCLUDED.call_spotlight_next_steps,
            call_spotlight_outcome = EXCLUDED.call_spotlight_outcome
        """, (
            conversation_key,
            call_data["id"],
            call_data.get("url"),
            call_data.get("direction"),
            call_data.get("disposition"),
            call_data.get("durationSeconds"),
            call_data.get("effectiveStartDateTime"),
            call_data.get("plannedStartDateTime"),
            call_data.get("plannedEndDateTime"),
            call_data.get("scope"),
            call_data.get("ownerId"),
            call_data.get("phoneNumber"),
            call_data.get("spotlight", {}).get("brief"),
            call_data.get("spotlight", {}).get("keyPoints"),
            json.dumps(call_data.get("spotlight", {}).get("nextSteps", [])),
            call_data.get("spotlight", {}).get("outcome"),
            call_data.get("spotlight", {}).get("type"),
            call_data.get("questionCompanyCount"),
            call_data.get("questionNonCompanyCount"),
            call_data.get("presentationDurationSec"),
            call_data.get("browserDurationSec"),
            call_data.get("webcamNonCompanyDurationSec")
        ))
        
        # Insert transcript if available
        if "transcript" in call_data:
            transcript_text = self.gong_client._extract_transcript_text(call_data["transcript"])
            
            cursor.execute("""
                INSERT INTO GONG_CALL_TRANSCRIPTS
                (conversation_key, transcript_json, transcript_text, 
                 language, recording_duration_sec)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (conversation_key) DO UPDATE SET
                transcript_json = EXCLUDED.transcript_json,
                transcript_text = EXCLUDED.transcript_text
            """, (
                conversation_key,
                json.dumps(call_data["transcript"]),
                transcript_text,
                call_data["transcript"].get("language"),
                call_data.get("durationSeconds")
            ))
    
    async def _insert_email_data(self, cursor, email_data: Dict[str, Any]):
        """Insert email-specific data"""
        conversation_key = email_data.get("conversationKey", f"email_{email_data['id']}")
        
        cursor.execute("""
            INSERT INTO GONG_EMAILS 
            (conversation_key, conversation_id, email_subject, email_thread_id,
             sender_email, recipient_emails, cc_emails, bcc_emails,
             email_direction, email_body_text, email_body_html,
             email_sentiment_score, email_attachment_count, 
             email_thread_position, reply_to_conversation_key)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (conversation_key) DO UPDATE SET
            email_sentiment_score = EXCLUDED.email_sentiment_score
        """, (
            conversation_key,
            email_data["id"],
            email_data.get("subject"),
            email_data.get("threadId"),
            email_data.get("senderEmail"),
            json.dumps(email_data.get("recipientEmails", [])),
            json.dumps(email_data.get("ccEmails", [])),
            json.dumps(email_data.get("bccEmails", [])),
            email_data.get("direction"),
            email_data.get("bodyText"),
            email_data.get("bodyHtml"),
            email_data.get("sentimentScore"),
            email_data.get("attachmentCount", 0),
            email_data.get("threadPosition"),
            email_data.get("replyToConversationKey")
        ))
    
    async def _insert_participants(self, cursor, conv: Dict[str, Any]):
        """Insert conversation participants"""
        conversation_key = conv.get("conversationKey", f"{conv['conversation_type']}_{conv['id']}")
        participants = conv.get("participants", [])
        
        for participant in participants:
            cursor.execute("""
                INSERT INTO GONG_PARTICIPANTS
                (conversation_key, participant_id, participant_name, 
                 participant_email, participant_role, participant_company,
                 is_from_customer, talk_time_percentage, email_role)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (conversation_key, participant_id) DO UPDATE SET
                participant_name = EXCLUDED.participant_name,
                participant_email = EXCLUDED.participant_email
            """, (
                conversation_key,
                participant.get("id"),
                participant.get("name"),
                participant.get("email"),
                participant.get("role"),
                participant.get("company"),
                participant.get("isFromCustomer", False),
                participant.get("talkTimePercentage"),
                participant.get("emailRole")
            ))
    
    async def _insert_trackers(self, cursor, conv: Dict[str, Any]):
        """Insert conversation trackers (topics/keywords)"""
        conversation_key = conv.get("conversationKey", f"{conv['conversation_type']}_{conv['id']}")
        trackers = conv.get("trackers", [])
        
        for tracker in trackers:
            cursor.execute("""
                INSERT INTO GONG_CONVERSATION_TRACKERS
                (conversation_key, tracker_id, tracker_name, 
                 tracker_type, tracker_count, tracker_sentiment)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (conversation_key, tracker_id) DO UPDATE SET
                tracker_count = EXCLUDED.tracker_count,
                tracker_sentiment = EXCLUDED.tracker_sentiment
            """, (
                conversation_key,
                tracker.get("id"),
                tracker.get("name"),
                tracker.get("type"),
                tracker.get("count", 1),
                tracker.get("sentiment")
            ))
    
    async def _insert_crm_context(self, cursor, conv: Dict[str, Any]):
        """Insert CRM context for conversation"""
        conversation_key = conv.get("conversationKey", f"{conv['conversation_type']}_{conv['id']}")
        contexts = conv.get("crmContexts", [])
        
        for context in contexts:
            cursor.execute("""
                INSERT INTO GONG_CONVERSATION_CONTEXTS
                (conversation_key, crm_object_type, crm_object_id, crm_object_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (conversation_key, crm_object_type, crm_object_id) DO NOTHING
            """, (
                conversation_key,
                context.get("type"),
                context.get("id"),
                context.get("name")
            ))
    
    async def _embed_and_store_conversations(self, conversations: List[Dict[str, Any]]):
        """Generate embeddings and store in Pinecone"""
        if not self.openai_client:
            self.logger.warning("OpenAI client not available. Skipping embeddings.")
            return
            
        vectors_to_upsert = []
        
        for conv in conversations:
            try:
                # Create context for embedding
                if conv["conversation_type"] == "call" and "transcript" in conv:
                    content = self.gong_client._extract_transcript_text(conv["transcript"])
                    content_type = "call_transcript"
                elif conv["conversation_type"] == "email":
                    content = f"Subject: {conv.get('subject', '')}\n\n{conv.get('bodyText', '')}"
                    content_type = "email_content"
                else:
                    # Skip if no meaningful content
                    continue
                
                # Truncate content if too long
                if len(content) > 8000:
                    content = content[:8000]
                
                # Generate embedding
                response = self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=content
                )
                
                embedding = response.data[0].embedding
                
                # Prepare vector for Pinecone
                vectors_to_upsert.append({
                    "id": f"{conv['conversation_type']}_{conv['id']}",
                    "values": embedding,
                    "metadata": {
                        "conversation_id": conv["id"],
                        "conversation_type": conv["conversation_type"],
                        "conversation_datetime": conv.get("dateTime"),
                        "content_type": content_type,
                        "participant_count": len(conv.get("participants", [])),
                        "trackers": [t.get("name") for t in conv.get("trackers", [])],
                    }
                })
                
            except Exception as e:
                self.logger.error(f"Failed to embed conversation {conv['id']}: {e}")
        
        # Batch upsert to Pinecone
        if vectors_to_upsert:
            self.pinecone_index.upsert(vectors=vectors_to_upsert)
            self.logger.info(f"Upserted {len(vectors_to_upsert)} conversation embeddings to Pinecone")
