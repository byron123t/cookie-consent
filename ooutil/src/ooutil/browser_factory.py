"""Utility to control browser."""

import contextlib
import os
from typing import AsyncGenerator

from playwright.async_api import async_playwright, Page

from ooutil.stealth.stealth_mode import make_stealth
from ooutil.user_agent import get_stealth_user_agent


@contextlib.asynccontextmanager
async def _get_page_or_context(get_page: bool, headless, stealth_mode=True, java_script_enabled=True, proxy=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, proxy=proxy)
        try:
            user_agent = get_stealth_user_agent() if stealth_mode else None
            context = await browser.new_context(user_agent=user_agent, java_script_enabled=java_script_enabled)
            if get_page:
                yield await context.new_page()
            else:
                yield context
        finally:
            await context.close()
            await browser.close()


@contextlib.asynccontextmanager
async def get_page(headless=True, stealth_mode=True, java_script_enabled=True, proxy=None) -> AsyncGenerator[Page, None]:
    """Get auto-close page. stealth_mode: avoid bot-detection of websites."""
    # Somehow navigator.stealth_mode not work
    async with _get_page_or_context(get_page=True, headless=headless, stealth_mode=stealth_mode, java_script_enabled=java_script_enabled, proxy=proxy) as page:
        if stealth_mode:
            await make_stealth(page)
        yield page
