"""Data Import and API Feed Handlers for Sophia AI Pay Ready Platform."""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Optional

import requests

logger = logging.getLogger(__name__)


class SlackDataImporter:
    """Import data from Slack API."""

    def __init__(self, token: str) -> None:
        self.token = token
        self.base = "https://slack.com/api"

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.get(f"{self.base}/{endpoint}", headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def fetch_users(self) -> Dict[str, Any]:
        return self._request("users.list")

    def fetch_channels(self) -> Dict[str, Any]:
        return self._request("conversations.list")

    def fetch_messages(self, channel: str) -> Dict[str, Any]:
        return self._request("conversations.history", {"channel": channel})


class GongDataImporter:
    """Import data from Gong.io API."""

    def __init__(self, token: str) -> None:
        self.token = token
        self.base = "https://api.gong.io"

    def _request(self, endpoint: str) -> Dict[str, Any]:
        headers = {"Authorization": f"token {self.token}"}
        resp = requests.get(f"{self.base}/{endpoint}", headers=headers)
        resp.raise_for_status()
        return resp.json()

    def fetch_calls(self) -> Dict[str, Any]:
        return self._request("v2/calls")

    def fetch_transcript(self, call_id: str) -> Dict[str, Any]:
        return self._request(f"v2/calls/{call_id}/transcript")


class GenericAPIImporter:
    """Generic importer for arbitrary JSON APIs."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def fetch(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/{path.lstrip('/')}", params=params)
        resp.raise_for_status()
        return resp.json()

    def batch_fetch(self, endpoints: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        results = {}
        for ep in endpoints:
            try:
                results[ep] = self.fetch(ep)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to fetch %s: %s", ep, exc)
        return results
