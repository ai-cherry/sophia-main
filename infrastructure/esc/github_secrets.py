"""Pulumi ESC Secret Manager for GitHub.
"""
from infrastructure.pulumi_esc import PulumiESCManager


class GitHubSecretManager(PulumiESCManager):
    def __init__(self):
        super().__init__()

    async def get_pat(self) -> str:
        return await self.get_secret("GITHUB_PAT")


github_secret_manager = GitHubSecretManager()
