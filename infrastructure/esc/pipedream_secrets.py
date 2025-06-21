"""Pulumi ESC Secret Manager for Pipedream.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class PipedreamSecretManager(PulumiESCManager):
    def __init__(self):
        super().__init__()

    async def get_api_key(self) -> str:
        return await self.get_secret("PIPEDREAM_API_KEY")


pipedream_secret_manager = PipedreamSecretManager()
