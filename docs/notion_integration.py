"""Notion Knowledge Base integration for Sophia AI Pay Ready Platform."""
from __future__ import annotations

import logging
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

NOTION_API_KEY = "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"
NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}


class NotionKnowledgeBase:
    """Simplified Notion API client."""

    def __init__(self) -> None:
        self.base = "https://api.notion.com/v1"

    def create_page(self, parent_db: str, title: str, blocks: list[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {
            "parent": {"database_id": parent_db},
            "properties": {"title": {"title": [{"text": {"content": title}}]}},
            "children": blocks,
        }
        resp = requests.post(f"{self.base}/pages", json=payload, headers=HEADERS)
        resp.raise_for_status()
        return resp.json()

    def append_block(self, page_id: str, blocks: list[Dict[str, Any]]) -> Dict[str, Any]:
        resp = requests.patch(f"{self.base}/blocks/{page_id}/children", json={"children": blocks}, headers=HEADERS)
        resp.raise_for_status()
        return resp.json()

    def simple_block(self, text: str) -> Dict[str, Any]:
        return {
            "object": "block",
            "paragraph": {"rich_text": [{"text": {"content": text}}]},
        }
