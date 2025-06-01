from pathlib import Path
import asyncio
import time

from playwright.async_api import Page

from ooutil.json_util import dump_to_json_file

from consent.har.har_capturer import get_har_capturer
from ooutil.browser_control import navigate_and_wait, scroll_to_bottom


async def goto_and_dump_cookies_har(page: Page, url: str, out_har_file: Path, out_json_file: Path, nav_wait_sec=5, do_scroll_to_bottom=True, verbose=0):
    """Go to a URL and dump both sent and browser cookies."""
    if verbose >= 1:
        print(f"Go to and dump cookies: {url=}")

    async with get_har_capturer(page, out_har_file):
        load_start_time = time.time()
        await navigate_and_wait(page, url)
        # Extra wait for fully loading/displaying banners
        await asyncio.sleep(nav_wait_sec)
        load_end_time = time.time()

        if do_scroll_to_bottom:
            await scroll_to_bottom(page)

        await asyncio.sleep(5)  # wait 5 sec for the page to render.

        dump_to_json_file({
                'url': page.url,
                'load_start_time': load_start_time,
                'load_end_time': load_end_time,
                'browser_cookies': await page.context.cookies()
            }, out_json_file)

        if verbose >= 1:
            print(f"Dumped cookies to file {out_json_file}")
