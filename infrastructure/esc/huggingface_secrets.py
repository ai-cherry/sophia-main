"""Pulumi ESC - Hugging Face Secret Management
Manages Hugging Face API keys.
"""
import logging
import os

import pulumi_pulumiservice as pulumiservice

from infrastructure.pulumi_esc import PulumiESCManager

logger = logging.getLogger(__name__)

PULUMI_ORG = os.getenv("PULUMI_ORG", "your-pulumi-org")
PULUMI_PROJECT = "sophia-ai"
PULUMI_STACK = "dev"
ENVIRONMENT_NAME = f"{PULUMI_PROJECT}-{PULUMI_STACK}"
HF_SECRET_NAME = "huggingFaceApiKey"

if PULUMI_ORG == "your-pulumi-org":
    raise ValueError("Please set the PULUMI_ORG environment variable.")


class HuggingFaceSecretManager(PulumiESCManager):
    """Manages Hugging Face secrets using Pulumi ESC."""

    def __init__(self):
        super().__init__()

    async def get_api_key(self) -> str:
        """Retrieves the Hugging Face API key from the Pulumi ESC environment.
        """
        try:
            opened_env = await pulumiservice.open_environment(
                name=ENVIRONMENT_NAME, organization=PULUMI_ORG
            )
            return opened_env.get(f"sophia.{HF_SECRET_NAME}")
        except Exception as e:
            logger.error(
                f"Failed to retrieve secret 'sophia.{HF_SECRET_NAME}' from Pulumi ESC: {e}"
            )
            api_key = os.getenv("HUGGING_FACE_API_KEY")
            if api_key:
                logger.warning(
                    "Falling back to HUGGING_FACE_API_KEY environment variable."
                )
                return api_key
            raise ConnectionError(
                "Could not retrieve Hugging Face API key from Pulumi ESC or environment variables."
            )


huggingface_secret_manager = HuggingFaceSecretManager()
