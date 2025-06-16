"""
Sophia AI - Slack Integration
Team communication and intelligent notification system

This module provides comprehensive Slack integration for Sophia AI,
enabling real-time team communication, intelligent notifications, and workflow automation.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.webhook.async_client import AsyncWebhookClient
from slack_sdk.signature import SignatureVerifier
import os
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SlackConfig(BaseModel):
    """Slack integration configuration"""
    bot_token: str = Field(default_factory=lambda: os.getenv('SLACK_BOT_TOKEN', ''))
    app_token: str = Field(default_factory=lambda: os.getenv('SLACK_APP_TOKEN', ''))
    signing_secret: str = Field(default_factory=lambda: os.getenv('SLACK_SIGNING_SECRET', ''))
    default_channel: str = Field(default='#sophia-notifications')
    notification_webhook_url: Optional[str] = Field(default_factory=lambda: os.getenv('SLACK_WEBHOOK_URL'))
    rate_limit_delay: float = 0.5  # 500ms between messages
    max_retries: int = 3

class SlackMessage(BaseModel):
    """Structured Slack message"""
    channel: str
    text: str
    blocks: Optional[List[Dict[str, Any]]] = None
    thread_ts: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    ephemeral_user: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SlackNotification(BaseModel):
    """Notification configuration"""
    type: str  # 'call_completed', 'deal_update', 'task_reminder', etc.
    priority: str  # 'low', 'medium', 'high', 'urgent'
    channel: Optional[str] = None
    mentions: List[str] = []
    data: Dict[str, Any]

class SlackIntegration:
    """Comprehensive Slack integration for Sophia AI"""
    
    def __init__(self, config: SlackConfig = None):
        self.config = config or SlackConfig()
        self.client = AsyncWebClient(token=self.config.bot_token)
        self.webhook_client = AsyncWebhookClient(self.config.notification_webhook_url) if self.config.notification_webhook_url else None
        self.signature_verifier = SignatureVerifier(self.config.signing_secret)
        self.last_message_time = datetime.now()
        self.notification_handlers: Dict[str, Callable] = {}
        self._channel_cache: Dict[str, str] = {}
        self._user_cache: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize Slack integration and test connection"""
        try:
            # Test authentication
            response = await self.client.auth_test()
            logger.info(f"Slack connection successful. Bot name: {response['user']}")
            
            # Cache channel list
            await self._cache_channels()
            
            return True
            
        except SlackApiError as e:
            logger.error(f"Failed to initialize Slack integration: {e.response['error']}")
            return False
    
    async def _cache_channels(self):
        """Cache channel list for quick lookups"""
        try:
            response = await self.client.conversations_list(types="public_channel,private_channel")
            
            for channel in response['channels']:
                self._channel_cache[channel['name']] = channel['id']
                self._channel_cache[channel['id']] = channel['name']
            
            logger.info(f"Cached {len(self._channel_cache) // 2} Slack channels")
            
        except SlackApiError as e:
            logger.error(f"Failed to cache channels: {e.response['error']}")
    
    # Message Sending
    async def send_message(self, message: SlackMessage) -> Optional[Dict[str, Any]]:
        """Send message to Slack channel"""
        try:
            # Rate limiting
            await self._rate_limit()
            
            # Resolve channel name to ID if needed
            channel_id = await self._resolve_channel(message.channel)
            
            # Send message
            kwargs = {
                'channel': channel_id,
                'text': message.text
            }
            
            if message.blocks:
                kwargs['blocks'] = message.blocks
            if message.thread_ts:
                kwargs['thread_ts'] = message.thread_ts
            if message.attachments:
                kwargs['attachments'] = message.attachments
            if message.metadata:
                kwargs['metadata'] = message.metadata
            
            response = await self.client.chat_postMessage(**kwargs)
            
            logger.info(f"Sent message to {message.channel}")
            return response.data
            
        except SlackApiError as e:
            logger.error(f"Failed to send message: {e.response['error']}")
            return None
    
    async def send_ephemeral_message(
        self, 
        channel: str, 
        user: str, 
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send ephemeral message visible only to specific user"""
        try:
            await self._rate_limit()
            
            channel_id = await self._resolve_channel(channel)
            user_id = await self._resolve_user(user)
            
            kwargs = {
                'channel': channel_id,
                'user': user_id,
                'text': text
            }
            
            if blocks:
                kwargs['blocks'] = blocks
            
            await self.client.chat_postEphemeral(**kwargs)
            return True
            
        except SlackApiError as e:
            logger.error(f"Failed to send ephemeral message: {e.response['error']}")
            return False
    
    async def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Update existing message"""
        try:
            channel_id = await self._resolve_channel(channel)
            
            kwargs = {
                'channel': channel_id,
                'ts': ts,
                'text': text
            }
            
            if blocks:
                kwargs['blocks'] = blocks
            
            await self.client.chat_update(**kwargs)
            return True
            
        except SlackApiError as e:
            logger.error(f"Failed to update message: {e.response['error']}")
            return False
    
    # Notification System
    async def send_notification(self, notification: SlackNotification) -> bool:
        """Send intelligent notification based on type and priority"""
        try:
            # Determine channel
            channel = notification.channel or self._get_channel_for_notification(notification)
            
            # Format message based on notification type
            message_data = await self._format_notification(notification)
            
            # Add mentions if needed
            if notification.mentions:
                mentions = ' '.join([f"<@{await self._resolve_user(user)}>" for user in notification.mentions])
                message_data['text'] = f"{mentions} {message_data['text']}"
            
            # Send via webhook for urgent notifications
            if notification.priority == 'urgent' and self.webhook_client:
                await self.webhook_client.send(**message_data)
            else:
                # Send via API
                message = SlackMessage(
                    channel=channel,
                    text=message_data['text'],
                    blocks=message_data.get('blocks'),
                    attachments=message_data.get('attachments')
                )
                await self.send_message(message)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
    
    async def _format_notification(self, notification: SlackNotification) -> Dict[str, Any]:
        """Format notification based on type"""
        formatters = {
            'call_completed': self._format_call_notification,
            'deal_update': self._format_deal_notification,
            'task_reminder': self._format_task_notification,
            'insight_alert': self._format_insight_notification,
            'system_alert': self._format_system_notification
        }
        
        formatter = formatters.get(notification.type, self._format_generic_notification)
        return await formatter(notification)
    
    async def _format_call_notification(self, notification: SlackNotification) -> Dict[str, Any]:
        """Format call completion notification"""
        data = notification.data
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📞 Call Analysis Complete"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Participants:*\n{data.get('participants', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Duration:*\n{data.get('duration', 0)} minutes"
                    }
                ]
            }
        ]
        
        # Add insights if available
        if data.get('insights'):
            insights = data['insights']
            
            if insights.get('key_topics'):
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Key Topics:*\n• " + "\n• ".join(insights['key_topics'][:3])
                    }
                })
            
            if insights.get('next_steps'):
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Next Steps:*\n• " + "\n• ".join(insights['next_steps'][:3])
                    }
                })
            
            if insights.get('success_probability'):
                emoji = "🟢" if insights['success_probability'] > 70 else "🟡" if insights['success_probability'] > 40 else "🔴"
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{emoji} *Success Probability:* {insights['success_probability']}%"
                    }
                })
        
        # Add action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View in CRM"},
                    "url": data.get('crm_link', '#'),
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Transcript"},
                    "url": data.get('transcript_link', '#')
                }
            ]
        })
        
        return {
            'text': f"Call analysis complete: {data.get('call_title', 'Sales Call')}",
            'blocks': blocks
        }
    
    async def _format_deal_notification(self, notification: SlackNotification) -> Dict[str, Any]:
        """Format deal update notification"""
        data = notification.data
        
        # Determine emoji based on update type
        emoji_map = {
            'stage_advanced': '🎯',
            'deal_won': '🎉',
            'deal_lost': '😔',
            'amount_updated': '💰',
            'at_risk': '⚠️'
        }
        emoji = emoji_map.get(data.get('update_type', ''), '📊')
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Deal Update: {data.get('deal_name', 'Unknown Deal')}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Company:*\n{data.get('company', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Amount:*\n${data.get('amount', 0):,.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Stage:*\n{data.get('current_stage', 'Unknown')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Close Date:*\n{data.get('close_date', 'TBD')}"
                    }
                ]
            }
        ]
        
        # Add context based on update type
        if data.get('update_details'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Update:* {data['update_details']}"
                }
            })
        
        return {
            'text': f"Deal update: {data.get('deal_name')} - {data.get('update_type', 'updated')}",
            'blocks': blocks
        }
    
    async def _format_task_notification(self, notification: SlackNotification) -> Dict[str, Any]:
        """Format task reminder notification"""
        data = notification.data
        
        urgency_emoji = {
            'overdue': '🚨',
            'today': '⏰',
            'upcoming': '📅'
        }
        emoji = urgency_emoji.get(data.get('urgency', ''), '📌')
        
        return {
            'text': f"{emoji} Task Reminder: {data.get('task_title', 'Task')}",
            'blocks': [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{emoji} *Task:* {data.get('task_title', 'Task')}\n"
                                f"*Due:* {data.get('due_date', 'No due date')}\n"
                                f"*Related to:* {data.get('related_to', 'N/A')}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Mark Complete"},
                            "action_id": f"complete_task_{data.get('task_id', '')}",
                            "style": "primary"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Snooze"},
                            "action_id": f"snooze_task_{data.get('task_id', '')}"
                        }
                    ]
                }
            ]
        }
    
    async def _format_insight_notification(self, notification: SlackNotification) -> Dict[str, Any]:
        """Format business insight notification"""
        data = notification.data
        
        return {
            'text': f"💡 Business Insight: {data.get('title', 'New Insight')}",
            'blocks': [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "💡 Business Insight Alert"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{data.get('title', 'Insight')}*\n\n{data.get('description', '')}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Impact:* {data.get('impact', 'Unknown')}\n"
                                f"*Recommendation:* {data.get('recommendation', 'Review needed')}"
                    }
                }
            ]
        }
    
    async def _format_system_notification(self, notification: SlackNotification) -> Dict[str, Any]:
        """Format system alert notification"""
        data = notification.data
        
        severity_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }
        emoji = severity_emoji.get(data.get('severity', 'info'), 'ℹ️')
        
        return {
            'text': f"{emoji} System Alert: {data.get('message', 'System notification')}",
            'attachments': [{
                'color': {
                    'info': '#36a64f',
                    'warning': '#ff9900',
                    'error': '#ff0000',
                    'success': '#36a64f'
                }.get(data.get('severity', 'info'), '#808080'),
                'text': data.get('details', '')
            }]
        }
    
    async def _format_generic_notification(self, notification: SlackNotification) -> Dict[str, Any]:
        """Format generic notification"""
        return {
            'text': notification.data.get('message', 'Sophia AI Notification'),
            'blocks': [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": notification.data.get('message', 'Notification from Sophia AI')
                    }
                }
            ]
        }
    
    def _get_channel_for_notification(self, notification: SlackNotification) -> str:
        """Determine appropriate channel based on notification type and priority"""
        channel_map = {
            'urgent': '#sophia-urgent',
            'deal_update': '#sales-updates',
            'call_completed': '#call-insights',
            'task_reminder': '#task-reminders',
            'system_alert': '#sophia-system'
        }
        
        # Check priority first
        if notification.priority == 'urgent':
            return channel_map.get('urgent', self.config.default_channel)
        
        # Then check type
        return channel_map.get(notification.type, self.config.default_channel)
    
    # Channel and User Management
    async def _resolve_channel(self, channel: str) -> str:
        """Resolve channel name to ID"""
        if channel.startswith('C') or channel.startswith('D'):
            return channel  # Already an ID
        
        channel_name = channel.lstrip('#')
        
        # Check cache first
        if channel_name in self._channel_cache:
            return self._channel_cache[channel_name]
        
        # Refresh cache and try again
        await self._cache_channels()
        return self._channel_cache.get(channel_name, channel)
    
    async def _resolve_user(self, user: str) -> str:
        """Resolve user email or name to ID"""
        if user.startswith('U'):
            return user  # Already an ID
        
        # Check cache first
        if user in self._user_cache:
            return self._user_cache[user]['id']
        
        try:
            # Look up by email
            response = await self.client.users_lookupByEmail(email=user)
            user_info = response['user']
            self._user_cache[user] = user_info
            return user_info['id']
        except:
            # Try to find by display name
            try:
                response = await self.client.users_list()
                for u in response['members']:
                    if u.get('real_name') == user or u.get('name') == user:
                        self._user_cache[user] = u
                        return u['id']
            except:
                pass
        
        return user  # Return as-is if can't resolve
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed user information"""
        try:
            response = await self.client.users_info(user=user_id)
            return response['user']
        except SlackApiError as e:
            logger.error(f"Failed to get user info: {e.response['error']}")
            return None
    
    async def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed channel information"""
        try:
            response = await self.client.conversations_info(channel=channel_id)
            return response['channel']
        except SlackApiError as e:
            logger.error(f"Failed to get channel info: {e.response['error']}")
            return None
    
    # Thread Management
    async def reply_to_thread(
        self,
        channel: str,
        thread_ts: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """Reply to existing thread"""
        message = SlackMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts,
            blocks=blocks
        )
        return await self.send_message(message)
    
    async def create_thread_with_replies(
        self,
        channel: str,
        initial_message: str,
        replies: List[str]
    ) -> Optional[str]:
        """Create thread with multiple replies"""
        try:
            # Send initial message
            message = SlackMessage(channel=channel, text=initial_message)
            response = await self.send_message(message)
            
            if not response:
                return None
            
            thread_ts = response['ts']
            
            # Send replies
            for reply in replies:
                await self.reply_to_thread(channel, thread_ts, reply)
                await asyncio.sleep(0.5)  # Small delay between replies
            
            return thread_ts
            
        except Exception as e:
            logger.error(f"Failed to create thread: {str(e)}")
            return None
    
    # Interactive Components
    async def handle_interaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle interactive component interactions (buttons, select menus, etc.)"""
        try:
            action_type = payload.get('type')
            
            if action_type == 'block_actions':
                return await self._handle_block_action(payload)
            elif action_type == 'view_submission':
                return await self._handle_view_submission(payload)
            elif action_type == 'shortcut':
                return await self._handle_shortcut(payload)
            else:
                logger.warning(f"Unknown interaction type: {action_type}")
                return {'response_action': 'clear'}
                
        except Exception as e:
            logger.error(f"Failed to handle interaction: {str(e)}")
            return {'response_action': 'clear'}
    
    async def _handle_block_action(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle block action (button click, etc.)"""
        actions = payload.get('actions', [])
        
        for action in actions:
            action_id = action.get('action_id', '')
            
            if action_id.startswith('complete_task_'):
                task_id = action_id.replace('complete_task_', '')
                await self._complete_task(task_id, payload)
            elif action_id.startswith('snooze_task_'):
                task_id = action_id.replace('snooze_task_', '')
                await self._snooze_task(task_id, payload)
        
        return {'response_action': 'update'}
    
    async def _complete_task(self, task_id: str, payload: Dict[str, Any]):
        """Handle task completion"""
        user = payload['user']['id']
        channel = payload['channel']['id']
        
        # Update message to show task completed
        await self.update_message(
            channel=channel,
            ts=payload['message']['ts'],
            text="✅ Task completed!",
            blocks=[{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✅ Task completed by <@{user}>"
                }
            }]
        )
    
    async def _snooze_task(self, task_id: str, payload: Dict[str, Any]):
        """Handle task snooze"""
        # Open modal for snooze duration selection
        await self.client.views_open(
            trigger_id=payload['trigger_id'],
            view={
                "type": "modal",
                "callback_id": f"snooze_task_modal_{task_id}",
                "title": {"type": "plain_text", "text": "Snooze Task"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "How long would you like to snooze this task?"},
                        "accessory": {
                            "type": "static_select",
                            "action_id": "snooze_duration",
                            "options": [
                                {"text": {"type": "plain_text", "text": "1 hour"}, "value": "1h"},
                                {"text": {"type": "plain_text", "text": "4 hours"}, "value": "4h"},
                                {"text": {"type": "plain_text", "text": "1 day"}, "value": "1d"},
                                {"text": {"type": "plain_text", "text": "3 days"}, "value": "3d"}
                            ]
                        }
                    }
                ],
                "submit": {"type": "plain_text", "text": "Snooze"}
            }
        )
    
    # Slash Commands
    async def handle_slash_command(self, command: str, text: str, user_id: str, channel_id: str) -> Dict[str, Any]:
        """Handle slash commands"""
        handlers = {
            '/sophia': self._handle_sophia_command,
            '/sophia-search': self._handle_search_command,
            '/sophia-insight': self._handle_insight_command,
            '/sophia-report': self._handle_report_command
        }
        
        handler = handlers.get(command)
        if handler:
            return await handler(text, user_id, channel_id)
        else:
            return {
                'response_type': 'ephemeral',
                'text': f"Unknown command: {command}"
            }
    
    async def _handle_sophia_command(self, text: str, user_id: str, channel_id: str) -> Dict[str, Any]:
        """Handle main /sophia command"""
        if not text:
            return {
                'response_type': 'ephemeral',
                'text': "Hi! I'm Sophia, your AI assistant. Try:\n"
                        "• `/sophia help` - Show available commands\n"
                        "• `/sophia status` - Check system status\n"
                        "• `/sophia analyze [topic]` - Get insights on a topic"
            }
        
        parts = text.split()
        subcommand = parts[0].lower()
        
        if subcommand == 'help':
            return await self._show_help()
        elif subcommand == 'status':
            return await self._show_status()
        elif subcommand == 'analyze':
            topic = ' '.join(parts[1:]) if len(parts) > 1 else 'general'
            return await self._analyze_topic(topic, user_id)
        else:
            return {
                'response_type': 'ephemeral',
                'text': f"Unknown subcommand: {subcommand}. Try `/sophia help`"
            }
    
    # Rate Limiting
    async def _rate_limit(self):
        """Implement rate limiting for Slack API"""
        elapsed = (datetime.now() - self.last_message_time).total_seconds()
        if elapsed < self.config.rate_limit_delay:
            await asyncio.sleep(self.config.rate_limit_delay - elapsed)
        self.last_message_time = datetime.now()
    
    # Webhook Verification
    def verify_webhook(self, timestamp: str, signature: str, body: str) -> bool:
        """Verify Slack webhook signature"""
        return self.signature_verifier.is_valid(
            body=body,
            timestamp=timestamp,
            signature=signature
        )
    
    # Event Handling
    async def handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack events"""
        event_type = event.get('type')
        
        handlers = {
            'message': self._handle_message_event,
            'app_mention': self._handle_mention_event,
            'reaction_added': self._handle_reaction_event
        }
        
        handler = handlers.get(event_type)
        if handler:
            return await handler(event)
        
        return {'status': 'ok'}
    
    async def _handle_message_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle message events"""
        # Skip bot messages to avoid loops
        if event.get('bot_id'):
            return {'status': 'ok'}
        
        text = event.get('text', '').lower()
        channel = event.get('channel')
        user = event.get('user')
        
        # Check for keywords that might need Sophia's attention
        keywords = ['sophia', 'help', 'analyze', 'insight', 'report']
        
        if any(keyword in text for keyword in keywords):
            # Respond to relevant messages
            await self.send_ephemeral_message(
                channel=channel,
                user=user,
                text="Hi! Did you need help? Try mentioning me directly with @Sophia or use `/sophia help`"
            )
        
        return {'status': 'ok'}
    
    async def _handle_mention_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle app mentions"""
        text = event.get('text', '')
        channel = event.get('channel')
        user = event.get('user')
        thread_ts = event.get('thread_ts') or event.get('ts')
        
        # Remove mention to get actual message
        import re
        clean_text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
        
        # Process the request
        response = await self._process_mention_request(clean_text, user)
        
        # Reply in thread
        await self.reply_to_thread(
            channel=channel,
            thread_ts=thread_ts,
            text=response
        )
        
        return {'status': 'ok'}
    
    async def _process_mention_request(self, text: str, user_id: str) -> str:
        """Process request from mention"""
        # This would integrate with Sophia's AI capabilities
        # For now, return a helpful response
        
        if 'report' in text.lower():
            return "I can help you generate reports! Try `/sophia-report sales` for a sales report."
        elif 'insight' in text.lower():
            return "Looking for insights? Use `/sophia-insight [topic]` to get AI-powered analysis."
        elif 'help' in text.lower():
            return "Here's what I can do:\n• Generate reports\n• Provide insights\n• Analyze calls\n• Track deals\n\nTry `/sophia help` for more details!"
        else:
            return f"Hi <@{user_id}>! I'm processing your request. For specific commands, try `/sophia help`"

# Example usage
if __name__ == "__main__":
    async def main():
        config = SlackConfig()
        slack = SlackIntegration(config)
        
        # Initialize
        if await slack.initialize():
            print("Slack integration initialized successfully")
            
            # Test sending a message
            message = SlackMessage(
                channel="#general",
                text="Hello from Sophia AI!",
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "👋 *Sophia AI is online!*\n\nI'm here to help with:\n• Call analysis\n• Deal tracking\n• Business insights"
                    }
                }]
            )
            
            result = await slack.send_message(message)
            if result:
                print(f"Message sent: {result['ts']}")
    
    asyncio.run(main())

