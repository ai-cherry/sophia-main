"""Pulumi ESC Secret Manager for Pulumi itself.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class PulumiSecretManager(PulumiESCManager):
    def __init__(self):
        super().__init__()

    async def get_access_token(self) -> str:
        return await self.get_secret("PULUMI_ACCESS_TOKEN")


pulumi_secret_manager = PulumiSecretManager()
