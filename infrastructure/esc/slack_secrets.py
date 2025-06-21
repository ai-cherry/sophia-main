"""Pulumi ESC Secret Manager for Slack.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class SlackSecretManager(PulumiESCManager):
    def __init__(self):
        super().__init__()

    async def get_bot_token(self) -> str:
        return await self.get_secret("SLACK_BOT_TOKEN")


slack_secret_manager = SlackSecretManager()
