"""Pulumi ESC Secret Manager for Apify.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class ApifySecretManager(PulumiESCManager):
    def __init__(self):
        super().__init__()

    async def get_api_key(self) -> str:
        return await self.get_secret("APIFY_API_KEY")


apify_secret_manager = ApifySecretManager()
