from pathlib import Path
from consent.har.har_capturer import NETWORK_ENABLE_METHOD, PAGE_ENABLE_METHOD, HarCapturer

import asyncio
from playwright.async_api import async_playwright, Page

async def run(playwright):
    browser = await playwright.chromium.launch()
    page: Page = await browser.new_page()

    har_file = Path(__file__).parent / 'test.har'
    har_capturer = await HarCapturer().from_page(page, har_file, [NETWORK_ENABLE_METHOD, PAGE_ENABLE_METHOD])

    try:
        await page.goto("https://www.unilever.com/accessibility/", timeout=4000)
        # print(await page.content())
    except Exception as e:
        pass
    finally:
        await har_capturer.detach()
        har_capturer.save()
        await browser.close()


async def main():
    async with async_playwright() as playwright:
        await run(playwright)

asyncio.run(main())