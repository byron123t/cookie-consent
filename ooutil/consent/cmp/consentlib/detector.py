from pathlib import Path
from typing import Dict, List, Optional, Type
import asyncio

from playwright.async_api import Page, TimeoutError

from consent.cmp.prefbtn.pref_btn_extractor import extract_pref_btn_selectors, extract_pref_btns
from consent.cmp.consentlib.consent_lib import ConsentLib
from consent.cmp.consentlib.factory import consent_lib_classes
from ooutil.browser_control import goto_ignore_timeout_error, try_click
from ooutil.async_util import asyncio_wait_for_timeout
from ooutil.url_util import get_netloc_path
from ooutil.page_util import get_btn_by_frame, is_link_to_other_page


async def get_consent_lib(page: Page, screenshot_file: Path=None, warnings: Optional[List]=None, verbose=2) -> Optional[ConsentLib]:
    """Look up a pref-btn database, or use the provided pref_btn_sel."""
    # Some site display on the top, so no need to extract pref btn.
    consent_lib = await create_consent_lib(page)
    if consent_lib is not None:
        if verbose >= 2: print(f'Found consent lib (no pref btn detection): {type(consent_lib)}]')
        return consent_lib

    # Scroll to bottom later because websites that use "consent on scroll" may hide the initial consent banners.
    await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
    if verbose >= 2: print("get_consent_lib scrolled to bottom.")
    await asyncio.sleep(3) # Wait for page to load.
    if screenshot_file is not None:
        await page.screenshot(path=screenshot_file)

    # pref_btns = await extract_pref_btns(page)
    frame_url_pref_btn_sels = await extract_pref_btn_selectors(page, warnings)

    initial_url = page.url
    # for pref_btn in pref_btns:
    for frame_url_pref_btn_sel in frame_url_pref_btn_sels:
        if isinstance(frame_url_pref_btn_sel, tuple):
            frame_url, pref_btn_sel = frame_url_pref_btn_sel
            if verbose >= 2: print(f"Consent Lib Detector: Try pref btn {frame_url=} {pref_btn_sel=}")
            pref_btn = await get_btn_by_frame(page, frame_url, pref_btn_sel, warnings)
        else:
            pref_btn = frame_url_pref_btn_sel

        if pref_btn is None:
            msg = f"Consent Lib Detector: Cannot retrieve pref btn from {frame_url=} {pref_btn_sel=}"
            if warnings: warnings.append(msg)
            if verbose >= 2: print(msg)
            continue

        if await is_link_to_other_page(pref_btn):
            if verbose >= 2: print(f'Consent Lib Detector: {pref_btn=} is a link to other page, skipping.')
            continue

        if not await try_click(pref_btn):
            if verbose >= 2: print("Fail to click pref btn.")
            continue

        if verbose >= 2:
            try:
                print(f"Clicked on a pref btn candidate. {await asyncio_wait_for_timeout(pref_btn.inner_html())}")
            except Exception as e:
                if warnings: warnings.append(f"Warning when try to print 'Clicked on a pref btn candidate': {e}")

        # Assume navigation to a new page iff netloc_paths are different.
        if get_netloc_path(page.url) != get_netloc_path(initial_url):
            # Tried to use frame.expect_navigation, but it still detected navigation on hbomax anyway.
            # raise ValueError("pref btn navigates to other page.")
            if verbose >= 2: print("Navigate to other page, go back to initial url")
            await goto_ignore_timeout_error(page, initial_url)
            continue

        await asyncio.sleep(5)  # wait for the menu fades in.

        consent_lib = await create_consent_lib(page)
        if consent_lib is not None:
            if verbose >= 2: print(f'Consent Lib Detector: Found consent lib {type(consent_lib)}]')
            break

    if screenshot_file is not None:
        await page.screenshot(path=screenshot_file)

    return consent_lib


async def create_consent_lib(page: Page) -> Optional[ConsentLib]:
    tasks = [asyncio.create_task(consent_lib_class.try_to_create(page)) for consent_lib_class in consent_lib_classes]
    for consent_lib in await asyncio.gather(*tasks):
        if consent_lib is not None:
            return consent_lib
    return None
