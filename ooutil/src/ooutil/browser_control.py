"""Async utilities for browsers."""

from io import BytesIO
from pathlib import Path
from multiprocessing import Lock
from typing import Dict, List
import asyncio
import json
import re
import time

from playwright.async_api import Error, async_playwright, Page, TimeoutError, ElementHandle, Request, BrowserContext, Route
from IPython.display import display
from PIL import Image
from ooutil.browser_factory import get_page

from ooutil.async_util import asyncio_wait_for_timeout
from ooutil.json_util import dump_to_json_file
from ooutil.user_agent import get_stealth_user_agent
from ooutil.wpr import get_wpr_proxied_browser
from ooutil.async_util import asyncio_wait_for_timeout


async def display_screenshot(page: Page):
    display(Image.open(BytesIO(await page.screenshot())))


async def goto_ignore_timeout_error(page: Page, url: str, timeout: float = None):
    """When timeout is None: use the default of the goto"""
    try:
        return await page.goto(url, wait_until="networkidle", timeout=timeout)
    except TimeoutError:
        pass

    return None


async def run_in_clean_browser(use_wpr: bool, headless: bool, url: str, func, *args, **kwargs):
    async with async_playwright() as p:
        if use_wpr:
            browser = await get_wpr_proxied_browser(p, headless=headless)
        else:
            browser = await p.chromium.launch(headless=headless)

        brcontext = await browser.new_context(user_agent=get_stealth_user_agent(browser))
        page = await brcontext.new_page()

        result = await func(brcontext, page, url, *args, **kwargs)

        await brcontext.close()
        await browser.close()

    return result


async def try_x(func, *args, **kwargs):
    """Try to do x."""
    try:
        await func(*args, **kwargs)
        return True
    except TimeoutError:
        pass
    return False


async def try_click_simple(el):
    """Try to click on el, return True if no timeout."""
    try:
        await el.click()
        return True
    except TimeoutError:
        pass
    return False


async def try_click(btn: ElementHandle, verbose=2):
    """Automatic detect preference button and click them. Return after successfully click one."""
    # Use this because Playwright (at least on version 1.22) clicked with error but then the button was not clicked.
    try:
        if verbose >= 2: print("Try to click by JS")
        await btn.evaluate_handle('e => e.click()')  # playwright click timeout
        return True
    except Exception as e:
        if verbose >= 2: print(e)

    try:
        if verbose >= 2: print("Try to playwright.click with force=True")
        await btn.click(force=True, timeout=5000) # Does not report error even if the click is unsuccessful due to hidden (warnerbros.com)
        return True
    except Exception as e:
        if verbose >= 2: print('click() timeout')

    if verbose >= 2: print("Try to click ...")
    try:
        await btn.click(timeout=5000)
        return True
    except Exception as e:
        if verbose >= 2: print(e)

    if verbose >= 2: print(f'Fail to click on {btn=}')
    return False


async def page_contains(page: Page, selector: str):
    try:
        # , state='attached', timeout=5000)
        founds = await page.query_selector_all(selector)
        return len(founds) > 0
    except TimeoutError:
        pass
    return False


class CookieIntercepter:
    def __init__(self, page: Page):
        self._page = page
        self._sent_cookies: List[Dict[str, str]] = []
        self._lock = Lock()

    async def __aenter__(self):
        # page.on('request') captures no cookies
        await self._page.route('**', self.intercept_cookies) # self._page.on('request', self.intercept_cookies)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        await self._page.unroute('**') # self._page.remove_listener("request", self.intercept_cookies)

    @property
    def sent_cookies(self):
        self._lock.acquire()
        try:
            return self._sent_cookies
        finally:
            self._lock.release()

    async def intercept_cookies(self, route: Route, request: Request, verbose=0):
        if verbose >= 4:
            print(f"CookieItercepter: {request.url=} {request.headers.get('cookie')=}")

        if (req_cookies := request.headers.get('cookie')) is not None:
            self._lock.acquire()
            try:
                self._sent_cookies.append(
                    {'request_url': request.url, 'cookie': req_cookies})
                if verbose >= 3:
                    print('=================' + request.url)
                    print(req_cookies)
            finally:
                self._lock.release()
        await route.continue_()


async def goto_and_dump_cookies(page: Page, url: str, out_file: Path, nav_wait_sec=5, verbose=0):
    """Go to a URL and dump both sent and browser cookies."""
    if verbose >= 1: print(f"Go to and dump cookies: {url=}")
    async with CookieIntercepter(page) as ci:
        load_start_time = time.time()
        await navigate_and_wait(page, url)
        await asyncio.sleep(nav_wait_sec) # Extra wait for fully loading/displaying banners
        load_end_time = time.time()

        await scroll_to_bottom(page)
        await asyncio.sleep(5)  # wait 5 sec for the page to render.

        dump_to_json_file({'url': page.url, 'load_start_time': load_start_time, 'load_end_time': load_end_time, 'browser_cookies': await page.context.cookies(), 'sent_cookies': ci.sent_cookies}, out_file)
        if verbose >= 1: print(f"Dumped cookies to file {out_file}")


async def get_selector(page: Page, el: ElementHandle, verbose=2):
    # await page.evaluate("async () => await import('https://medv.io/finder/finder.js').then(m => finder = m)") # not work on facebook.com
    finder_file = Path(__file__).parent / 'finder.js'
    assert finder_file.exists(), f'The finder.js script must present in the same directory.'
    finder_script = finder_file.read_text()

    # Try to use owning frame
    frame = await el.owner_frame()
    if frame is None:
        if verbose >= 2: print(f"Cannot get owner frame of {el}")
        return None

    use_eval = True  # Using False sometimes yields an error: __finder not found.
    if use_eval:
        # Evaluate directly may have conflict with website.
        finder_script = re.sub('export function finder', 'function finder', finder_script)
        await frame.evaluate(finder_script)
        return frame.url, await el.evaluate("async (e) => await finder(e, {seedMinLength:4})")
    else:
        # Loading from network: may need to wait for finder to load.
        # await page.add_script_tag(content='import {finder} from "https://medv.io/finder/finder.js"; window.finder = finder', type='module')
        # TODO: retry if _finder not defined.

        # using page worked but sometimes failed.
        # await page.add_script_tag(content=finder_script + '\nwindow.__finder = finder;', type='module') # export finder to window

        if verbose >= 3: print('get_selector: Frame add script tag')
        await frame.add_script_tag(content=finder_script + '\nwindow.__finder = finder;', type='module') # export finder to window.

        # await asyncio.sleep(3)  # does not help.
        selector = await el.evaluate("async (e) => await __finder(e, {seedMinLength:4})")
        if verbose >= 3: print(f'selector: {selector}')
        return frame.url, selector
        # return [await page.evaluate("async (e) => await finder(e, {seedMinLength:4})", el) for el in elements]

async def get_context_cookies(browser_context: BrowserContext):
    return await browser_context.cookies()

async def get_page_cookies(page: Page):
    return await get_context_cookies(page.context)

async def get_page_html(page: Page):
    return await page.content()


async def get_html_from_url(url: str, headless=True, stealth_mode=True, verbose=2):
    async with get_page(headless=headless, stealth_mode=stealth_mode) as page:
        response = await goto_ignore_timeout_error(page, url)
        if response is None:
            return None
        if verbose >= 2: print(page)
        return await get_page_html(page)


async def get_frame_htmls_from_url(url: str, headless=True, stealth_mode=True, verbose=2):
    async with get_page(headless=headless, stealth_mode=stealth_mode) as page:
        response = await goto_ignore_timeout_error(page, url)
        if response is None:
            return None
        if verbose >= 2: print(page)
        return await get_frame_htmls(page)


async def get_frame_htmls(page: Page):
    frame_htmls = []
    for frame in page.frames:
        frame_content = await asyncio_wait_for_timeout(frame.content())
        if frame_content is not None:
            frame_htmls.append({'url': frame.url, 'html': frame_content})
    return frame_htmls


async def get_outer_html(el: ElementHandle):
    # TODO: use ooutil.browser_control.get_selector()
    try:
        return await asyncio.wait_for(el.evaluate("e => e.outerHTML"), timeout=5)
    except (asyncio.TimeoutError, TimeoutError) as e:
        print("WARNING: getting outer html timed out")
    return None


async def scroll_to_bottom(page):
    await asyncio_wait_for_timeout(page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)"))


def tag(atag):
    return f'[{atag}] ' if atag is not None else ''


ERROR_REASON_EMPTY_BODY = 'empty body'
async def navigate_and_wait(page: Page, url, result=None, url_tag=None, verbose=2):
    if verbose >= 2:
        print('Go to', url)

    try:
        response = await page.goto(url=url, wait_until='networkidle', timeout=60000) # 30000 for us, 60000 for eu
        status = response.status if response else None
        if status != 200:
            raise ValueError(
                f'{tag(url_tag)}Response status is not success (200 code), got status {status}')
    except TimeoutError:
        if result is not None:
            result.warnings.append(f'{tag(url_tag)}Navigation timeout')

    ABOUT_BLANK_URL = 'about:blank'
    if page.url == ABOUT_BLANK_URL:
        raise ValueError(
            f'{tag(url_tag)}Navigation error, navigated to {ABOUT_BLANK_URL}')

    # Check if the page is loaded properly.
    body_text = None
    try:
        if verbose >= 3: print('Getting body')
        body_text = await page.text_content('body', timeout=10000)
        if verbose >= 3: print('Finished getting body')
        if verbose >= 3: print(type(body_text), body_text)
    except TimeoutError:
        pass

    if body_text is None:
        msg = f'{tag(url_tag)}Loading error, cannot retrieve body text.' # {await page.content()=}' # page.content() may timeout, avoid this
        if verbose >= 2: print(msg)
        raise ValueError(msg)
    else:
        # Some cases like tencent.com has an empty body.
        if len(body_text) == 0:
            raise ValueError(f'{tag(url_tag)}{ERROR_REASON_EMPTY_BODY}')

async def is_input_checked(input_el: ElementHandle) -> bool:
    # From http://help.dottoro.com/ljpiwrem.php and stackoverflow
    return await input_el.evaluate("node => node.checked")


async def try_get_attribute(element: ElementHandle, attr: str, value_error_msg: str=None):
    """Raise Value Error if value_error_msg is provided."""
    try:
        val = await asyncio_wait_for_timeout(element.get_attribute(attr), default_val=None)
        if val is None and value_error_msg is not None:
            raise ValueError(value_error_msg)
        return val
    except TimeoutError:
        pass
    return None


async def try_get_one_element(page: Page, selectors: List[str], state='visible', timeout=5000):
    """Return the first element that match one of the selectors."""
    for selector in selectors:
        try:
            el = await page.wait_for_selector(selector, state=state, timeout=timeout)
            if el is not None:
                return el
        except TimeoutError:
            pass
    return None

async def take_screenshot_ignore_timeout(page: Page, path: Path, verbose=2):
    try:
        await page.screenshot(path=path)
    except TimeoutError as e:
        if verbose >= 2:
            print(f"Timeout taking screenshot to {path}:", e)

async def get_local_storage_key(page: Page, key: str, get_json_dict=False):
    local_storage_str = await page.evaluate(f"window.localStorage.getItem('{key}')")
    if get_json_dict:
        return json.loads(local_storage_str)
    return local_storage_str

async def save_storage_state(page: Page, out_file: Path):
    await page.context.storage_state(path=out_file)
