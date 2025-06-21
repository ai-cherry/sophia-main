"""Pulumi ESC Secret Manager for Estuary.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class EstuarySecretManager(PulumiESCManager):
    def __init__(self):
        super().__init__()

    async def get_api_key(self) -> str:
        return await self.get_secret("ESTUARY_API_KEY")


estuary_secret_manager = EstuarySecretManager()
