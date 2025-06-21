"""Pulumi ESC Secret Manager for Gong.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class GongSecretManager(PulumiESCManager):
    def __init__(self):
        super().__init__()

    async def get_api_key(self) -> str:
        return await self.get_secret("GONG_API_KEY")


gong_secret_manager = GongSecretManager()
