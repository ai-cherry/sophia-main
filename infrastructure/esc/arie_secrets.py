"""Pulumi ESC Secret Manager for Arie.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class ArieSecretManager(PulumiESCManager):
    def __init__(self):
        super().__init__()

    async def get_api_key(self) -> str:
        return await self.get_secret("ARIE_API_KEY")


arie_secret_manager = ArieSecretManager()
