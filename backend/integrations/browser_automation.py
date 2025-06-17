"""Browser automation utilities using Apify and Playwright."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from playwright.async_api import async_playwright, Browser
from apify_client import ApifyClient

logger = logging.getLogger(__name__)


class BrowserAutomation:
    def __init__(self, apify_token: str | None = None) -> None:
        self.apify_client = ApifyClient(apify_token) if apify_token else None
        self._playwright = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def run_apify_actor(self, actor_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.apify_client:
            raise RuntimeError("Apify client not configured")
        run = self.apify_client.actor(actor_id).call(run_input=input_data)
        return run

    async def simple_navigation(self, url: str) -> str:
        if not self._browser:
            await self.start()
        page = await self._browser.new_page()
        await page.goto(url)
        content = await page.content()
        await page.close()
        return content
