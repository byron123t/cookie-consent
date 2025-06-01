"""Util for Playwright pages."""


from typing import List, Optional

from playwright.async_api import ElementHandle, Frame, Page

from ooutil.async_util import asyncio_wait_for_timeout
from ooutil.browser_control import get_selector


def get_frame_by_url(page: Page, frame_url: str) -> Optional[Frame]:
    for frame in page.frames:
        if frame.url == frame_url:
            return frame
    return None


async def get_btn_by_frame(page: Page, frame_url: str, btn_sel: str, warnings: Optional[List] = None) -> Optional[ElementHandle]:
    frame = get_frame_by_url(page, frame_url)
    if frame is None:
        return None

    try:
        return await frame.wait_for_selector(btn_sel, timeout=5000)
    # except TimeoutError:
    except Exception as e:
        if warnings:
            warnings.append(f"Failed to get_btn_by_frame: {e}")

    return None


async def is_link_to_other_page(btn: ElementHandle):
    """Quick check whether the btn is a link to another page"""
    try:
        href = await btn.get_attribute('href')
        # removed: e.g., https://www.hbomax.com/#compliance-link
        return href is not None and len(href) and not href.startswith('#') and not href.startswith('javascript:') and 'Cookiebot.renew()' not in href
    except Exception as e:
        print("is_link_to_other_page error", e)
    return False


async def get_opt_btn_selectors(page, btns, warnings, verbose=2):
    """Return (frame_url, selector in the frame)
    Return a list so that the caller can await.
    """
    results = []
    for btn in btns:
        try:
            result = await asyncio_wait_for_timeout(get_selector(page, btn))
            if result is not None:
                results.append(result)
        except Exception as e:
            msg = f"Error extract btns: {e}"
            if verbose >= 2: print(msg)
            if warnings: warnings.append(msg)
    return results
