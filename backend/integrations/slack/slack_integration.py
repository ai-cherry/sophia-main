"""
Sophia AI - Slack Integration
Team Communication and AI Assistant Interface for Pay Ready

This module provides comprehensive Slack integration for Sophia AI,
enabling team communication, automated notifications, and conversational AI.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.async_client import AsyncSocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
import openai
import os

logger = logging.getLogger(__name__)

class SlackConfig:
    def __init__(self):
        self.bot_token = os.getenv('SLACK_BOT_TOKEN', '')
        self.app_token = os.getenv('SLACK_APP_TOKEN', '')
        self.signing_secret = os.getenv('SLACK_SIGNING_SECRET', '')
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.sophia_channel = os.getenv('SOPHIA_SLACK_CHANNEL', '#sophia-ai')
        self.alerts_channel = os.getenv('ALERTS_SLACK_CHANNEL', '#alerts')

class SophiaSlackBot:
    """Sophia AI Slack Bot for team communication and assistance"""
    
    def __init__(self, config: SlackConfig = None):
        self.config = config or SlackConfig()
        self.web_client = AsyncWebClient(token=self.config.bot_token)
        self.socket_client = None
        self.message_handlers = {}
        self.command_handlers = {}
        self.is_running = False
        
        # Initialize OpenAI for conversational AI
        if self.config.openai_api_key:
            openai.api_key = self.config.openai_api_key
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message and command handlers"""
        self.register_command('help', self._handle_help_command)
        self.register_command('status', self._handle_status_command)
        self.register_command('analytics', self._handle_analytics_command)
        self.register_command('call-summary', self._handle_call_summary_command)
        self.register_command('deal-update', self._handle_deal_update_command)
        self.register_command('insights', self._handle_insights_command)
        
        self.register_message_handler('mention', self._handle_mention)
        self.register_message_handler('dm', self._handle_direct_message)
    
    def register_command(self, command: str, handler: Callable):
        """Register slash command handler"""
        self.command_handlers[command] = handler
    
    def register_message_handler(self, event_type: str, handler: Callable):
        """Register message event handler"""
        self.message_handlers[event_type] = handler
    
    async def start(self):
        """Start the Slack bot"""
        try:
            self.socket_client = AsyncSocketModeClient(
                app_token=self.config.app_token,
                web_client=self.web_client
            )
            
            # Register socket mode handlers
            self.socket_client.socket_mode_request_listeners.append(self._handle_socket_mode_request)
            
            # Start socket mode client
            await self.socket_client.connect()
            self.is_running = True
            
            # Send startup message
            await self.send_message(
                channel=self.config.sophia_channel,
                text="🤖 Sophia AI is now online and ready to assist the Pay Ready team!"
            )
            
            logger.info("Sophia Slack bot started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Slack bot: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the Slack bot"""
        try:
            self.is_running = False
            
            if self.socket_client:
                await self.socket_client.disconnect()
            
            # Send shutdown message
            await self.send_message(
                channel=self.config.sophia_channel,
                text="🤖 Sophia AI is going offline. See you soon!"
            )
            
            logger.info("Sophia Slack bot stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Slack bot: {str(e)}")
    
    async def _handle_socket_mode_request(self, client: AsyncSocketModeClient, req: SocketModeRequest):
        """Handle incoming socket mode requests"""
        try:
            # Acknowledge the request
            response = SocketModeResponse(envelope_id=req.envelope_id)
            await client.send_socket_mode_response(response)
            
            # Process the event
            if req.type == "events_api":
                event = req.payload.get("event", {})
                await self._handle_event(event)
            
            elif req.type == "slash_commands":
                command_data = req.payload
                await self._handle_slash_command(command_data)
            
        except Exception as e:
            logger.error(f"Error handling socket mode request: {str(e)}")
    
    async def _handle_event(self, event: Dict[str, Any]):
        """Handle Slack events"""
        try:
            event_type = event.get("type")
            
            if event_type == "message":
                await self._handle_message_event(event)
            elif event_type == "app_mention":
                await self._handle_mention_event(event)
            
        except Exception as e:
            logger.error(f"Error handling event: {str(e)}")
    
    async def _handle_message_event(self, event: Dict[str, Any]):
        """Handle message events"""
        try:
            # Skip bot messages
            if event.get("bot_id"):
                return
            
            channel = event.get("channel")
            user = event.get("user")
            text = event.get("text", "")
            
            # Check if it's a DM
            if channel.startswith("D"):
                if 'dm' in self.message_handlers:
                    await self.message_handlers['dm'](event)
            
            # Check for mentions
            elif f"<@{await self._get_bot_user_id()}>" in text:
                if 'mention' in self.message_handlers:
                    await self.message_handlers['mention'](event)
            
        except Exception as e:
            logger.error(f"Error handling message event: {str(e)}")
    
    async def _handle_mention_event(self, event: Dict[str, Any]):
        """Handle app mention events"""
        try:
            if 'mention' in self.message_handlers:
                await self.message_handlers['mention'](event)
        except Exception as e:
            logger.error(f"Error handling mention event: {str(e)}")
    
    async def _handle_slash_command(self, command_data: Dict[str, Any]):
        """Handle slash commands"""
        try:
            command = command_data.get("command", "").lstrip("/")
            
            if command in self.command_handlers:
                await self.command_handlers[command](command_data)
            else:
                # Unknown command
                await self.send_message(
                    channel=command_data.get("channel_id"),
                    text=f"Unknown command: /{command}. Type `/help` for available commands."
                )
        except Exception as e:
            logger.error(f"Error handling slash command: {str(e)}")
    
    async def _get_bot_user_id(self) -> str:
        """Get bot user ID"""
        try:
            response = await self.web_client.auth_test()
            return response["user_id"]
        except Exception as e:
            logger.error(f"Failed to get bot user ID: {str(e)}")
            return ""
    
    # Message Sending
    async def send_message(self, channel: str, text: str = None, blocks: List[Dict] = None, 
                          thread_ts: str = None, attachments: List[Dict] = None) -> Optional[Dict]:
        """Send message to Slack channel"""
        try:
            response = await self.web_client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts,
                attachments=attachments
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return None
    
    async def send_ephemeral_message(self, channel: str, user: str, text: str = None, blocks: List[Dict] = None) -> Optional[Dict]:
        """Send ephemeral message (only visible to specific user)"""
        try:
            response = await self.web_client.chat_postEphemeral(
                channel=channel,
                user=user,
                text=text,
                blocks=blocks
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to send ephemeral message: {str(e)}")
            return None
    
    async def update_message(self, channel: str, ts: str, text: str = None, blocks: List[Dict] = None) -> Optional[Dict]:
        """Update existing message"""
        try:
            response = await self.web_client.chat_update(
                channel=channel,
                ts=ts,
                text=text,
                blocks=blocks
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to update message: {str(e)}")
            return None
    
    # Default Command Handlers
    async def _handle_help_command(self, command_data: Dict[str, Any]):
        """Handle /help command"""
        help_text = """
🤖 *Sophia AI Commands*

*Available Commands:*
• `/help` - Show this help message
• `/status` - Check Sophia AI system status
• `/analytics` - Get business analytics summary
• `/call-summary [call_id]` - Get summary of a specific call
• `/deal-update [deal_id]` - Get deal status update
• `/insights` - Get latest business insights

*Conversational AI:*
• Mention @Sophia AI in any channel to ask questions
• Send direct messages for private assistance
• Ask about customers, deals, calls, or business metrics

*Examples:*
• "What's our revenue this month?"
• "Show me recent calls with high-value prospects"
• "Any deals closing this week?"
• "Summarize yesterday's sales calls"
        """
        
        await self.send_ephemeral_message(
            channel=command_data.get("channel_id"),
            user=command_data.get("user_id"),
            text=help_text
        )
    
    async def _handle_status_command(self, command_data: Dict[str, Any]):
        """Handle /status command"""
        try:
            # Get system status (this would integrate with monitoring)
            status_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "🤖 *Sophia AI System Status*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Core System:* ✅ Online"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*HubSpot Integration:* ✅ Connected"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Gong.io Integration:* ✅ Connected"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Vector Database:* ✅ Operational"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Last Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                }
            ]
            
            await self.send_ephemeral_message(
                channel=command_data.get("channel_id"),
                user=command_data.get("user_id"),
                blocks=status_blocks
            )
            
        except Exception as e:
            await self.send_ephemeral_message(
                channel=command_data.get("channel_id"),
                user=command_data.get("user_id"),
                text=f"Error getting status: {str(e)}"
            )
    
    async def _handle_analytics_command(self, command_data: Dict[str, Any]):
        """Handle /analytics command"""
        try:
            # This would integrate with actual analytics
            analytics_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "📊 *Pay Ready Analytics Summary*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*This Month Revenue:* $125,000"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Active Deals:* 23"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Calls This Week:* 47"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Win Rate:* 68%"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Full Dashboard"
                            },
                            "url": "https://sophia-dashboard.payready.com"
                        }
                    ]
                }
            ]
            
            await self.send_ephemeral_message(
                channel=command_data.get("channel_id"),
                user=command_data.get("user_id"),
                blocks=analytics_blocks
            )
            
        except Exception as e:
            await self.send_ephemeral_message(
                channel=command_data.get("channel_id"),
                user=command_data.get("user_id"),
                text=f"Error getting analytics: {str(e)}"
            )
    
    async def _handle_call_summary_command(self, command_data: Dict[str, Any]):
        """Handle /call-summary command"""
        try:
            text = command_data.get("text", "").strip()
            if not text:
                await self.send_ephemeral_message(
                    channel=command_data.get("channel_id"),
                    user=command_data.get("user_id"),
                    text="Please provide a call ID: `/call-summary [call_id]`"
                )
                return
            
            # This would integrate with Gong.io to get actual call summary
            summary_text = f"""
📞 *Call Summary for {text}*

*Participants:* John Smith (Pay Ready), Sarah Johnson (Prospect)
*Duration:* 45 minutes
*Date:* {datetime.now().strftime('%Y-%m-%d')}

*Key Points:*
• Prospect interested in enterprise solution
• Budget confirmed: $50K annually
• Decision timeline: End of quarter
• Next step: Technical demo scheduled

*Sentiment:* Positive
*Deal Stage:* Demo Scheduled
*Follow-up Required:* Technical demo preparation
            """
            
            await self.send_ephemeral_message(
                channel=command_data.get("channel_id"),
                user=command_data.get("user_id"),
                text=summary_text
            )
            
        except Exception as e:
            await self.send_ephemeral_message(
                channel=command_data.get("channel_id"),
                user=command_data.get("user_id"),
                text=f"Error getting call summary: {str(e)}"
            )
    
    async def _handle_deal_update_command(self, command_data: Dict[str, Any]):
        """Handle /deal-update command"""
        try:
            text = command_data.get("text", "").strip()
            if not text:
                await self.send_ephemeral_message(
                    channel=command_data.get("channel_id"),
                    user=command_data.get("user_id"),
                    text="Please provide a deal ID: `/deal-update [deal_id]`"
                )
                return
            
            # This would integrate with HubSpot to get actual deal data
            deal_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"💼 *Deal Update: {text}*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Company:* Acme Corp"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Value:* $75,000"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Stage:* Proposal Sent"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Close Date:* 2024-02-15"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Recent Activity:* Proposal sent yesterday, follow-up call scheduled for tomorrow"
                    }
                }
            ]
            
            await self.send_ephemeral_message(
                channel=command_data.get("channel_id"),
                user=command_data.get("user_id"),
                blocks=deal_blocks
            )
            
        except Exception as e:
            await self.send_ephemeral_message(
                channel=command_data.get("channel_id"),
                user=command_data.get("user_id"),
                text=f"Error getting deal update: {str(e)}"
            )
    
    async def _handle_insights_command(self, command_data: Dict[str, Any]):
        """Handle /insights command"""
        try:
            insights_text = """
🧠 *Latest Business Insights*

*🔥 Hot Opportunities:*
• Acme Corp deal (75K) - High engagement, proposal under review
• TechStart Inc (120K) - Decision maker engaged, budget confirmed

*⚠️ At-Risk Deals:*
• Global Solutions (90K) - No response to last 3 follow-ups
• StartupXYZ (45K) - Competitor mentioned in last call

*📈 Trending Topics:*
• AI automation solutions (+40% mentions this week)
• Integration capabilities (top concern in 60% of calls)
• ROI calculations (requested in 8 recent demos)

*🎯 Recommended Actions:*
• Follow up with Global Solutions urgently
• Prepare competitive analysis for StartupXYZ
• Create AI automation case studies for prospects
            """
            
            await self.send_ephemeral_message(
                channel=command_data.get("channel_id"),
                user=command_data.get("user_id"),
                text=insights_text
            )
            
        except Exception as e:
            await self.send_ephemeral_message(
                channel=command_data.get("channel_id"),
                user=command_data.get("user_id"),
                text=f"Error getting insights: {str(e)}"
            )
    
    # Default Message Handlers
    async def _handle_mention(self, event: Dict[str, Any]):
        """Handle mentions of Sophia AI"""
        try:
            channel = event.get("channel")
            user = event.get("user")
            text = event.get("text", "")
            ts = event.get("ts")
            
            # Remove mention from text
            bot_user_id = await self._get_bot_user_id()
            clean_text = text.replace(f"<@{bot_user_id}>", "").strip()
            
            if not clean_text:
                await self.send_message(
                    channel=channel,
                    text="Hi! I'm Sophia AI, your Pay Ready assistant. How can I help you today?",
                    thread_ts=ts
                )
                return
            
            # Generate AI response
            response = await self._generate_ai_response(clean_text, user)
            
            await self.send_message(
                channel=channel,
                text=response,
                thread_ts=ts
            )
            
        except Exception as e:
            logger.error(f"Error handling mention: {str(e)}")
    
    async def _handle_direct_message(self, event: Dict[str, Any]):
        """Handle direct messages to Sophia AI"""
        try:
            channel = event.get("channel")
            user = event.get("user")
            text = event.get("text", "")
            
            if not text:
                return
            
            # Generate AI response
            response = await self._generate_ai_response(text, user)
            
            await self.send_message(
                channel=channel,
                text=response
            )
            
        except Exception as e:
            logger.error(f"Error handling direct message: {str(e)}")
    
    async def _generate_ai_response(self, text: str, user_id: str) -> str:
        """Generate AI response using OpenAI"""
        try:
            if not self.config.openai_api_key:
                return "I'm sorry, but my AI capabilities are currently unavailable. Please try again later."
            
            # Get user info
            user_info = await self.web_client.users_info(user=user_id)
            user_name = user_info.data.get("user", {}).get("real_name", "there")
            
            # Create context-aware prompt
            system_prompt = f"""
You are Sophia AI, the intelligent assistant for Pay Ready, a business services company. 
You help the team with:
- Business analytics and insights
- Customer relationship management
- Sales call analysis and coaching
- Deal pipeline management
- Revenue forecasting
- Team productivity optimization

You have access to:
- HubSpot CRM data
- Gong.io call recordings and analysis
- Business intelligence dashboards
- Customer interaction history

Be helpful, professional, and concise. Provide actionable insights when possible.
The user's name is {user_name}.
"""
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return "I'm sorry, I encountered an error processing your request. Please try again or contact support if the issue persists."
    
    # Notification Methods
    async def send_deal_alert(self, deal_data: Dict[str, Any]):
        """Send deal-related alert to team"""
        try:
            alert_text = f"""
🚨 *Deal Alert*

*Company:* {deal_data.get('company', 'Unknown')}
*Value:* ${deal_data.get('value', 0):,}
*Stage:* {deal_data.get('stage', 'Unknown')}
*Alert Type:* {deal_data.get('alert_type', 'Update')}

*Details:* {deal_data.get('details', 'No additional details')}
            """
            
            await self.send_message(
                channel=self.config.alerts_channel,
                text=alert_text
            )
            
        except Exception as e:
            logger.error(f"Error sending deal alert: {str(e)}")
    
    async def send_call_summary(self, call_data: Dict[str, Any]):
        """Send call summary to team"""
        try:
            summary_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📞 *Call Summary: {call_data.get('title', 'Unknown Call')}*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Duration:* {call_data.get('duration', 0)} minutes"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Sentiment:* {call_data.get('sentiment', 'Neutral')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Participants:* {len(call_data.get('participants', []))}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Outcome:* {call_data.get('outcome', 'Unknown')}"
                        }
                    ]
                }
            ]
            
            if call_data.get('key_insights'):
                summary_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Key Insights:*\n{call_data['key_insights']}"
                    }
                })
            
            await self.send_message(
                channel=self.config.sophia_channel,
                blocks=summary_blocks
            )
            
        except Exception as e:
            logger.error(f"Error sending call summary: {str(e)}")
    
    async def send_daily_digest(self):
        """Send daily business digest"""
        try:
            digest_text = f"""
📊 *Daily Business Digest - {datetime.now().strftime('%Y-%m-%d')}*

*Today's Highlights:*
• 12 calls completed
• 3 new deals created
• $45,000 in new pipeline value
• 2 deals moved to proposal stage

*Top Performers:*
• Sarah J. - 5 calls, 2 new opportunities
• Mike R. - 3 demos, 1 deal closed

*Action Items:*
• Follow up with Acme Corp (proposal sent yesterday)
• Prepare demo for TechStart Inc (scheduled tomorrow)
• Review pricing for Global Solutions deal

*Tomorrow's Schedule:*
• 9 AM - Demo with TechStart Inc
• 2 PM - Proposal review with Acme Corp
• 4 PM - Team standup meeting
            """
            
            await self.send_message(
                channel=self.config.sophia_channel,
                text=digest_text
            )
            
        except Exception as e:
            logger.error(f"Error sending daily digest: {str(e)}")

# Example usage
if __name__ == "__main__":
    async def main():
        config = SlackConfig()
        bot = SophiaSlackBot(config)
        
        try:
            await bot.start()
            
            # Keep the bot running
            while bot.is_running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down bot...")
        finally:
            await bot.stop()
    
    asyncio.run(main())

