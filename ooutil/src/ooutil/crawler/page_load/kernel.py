"""Page Loader."""

import asyncio
import json

from playwright.async_api import Frame, Page, TimeoutError

from ooutil.crawler.page_load.result import PageLoadResult
from ooutil.crawler.scanner import Scanner
from ooutil.image import encode_to_base64
from ooutil.browser_control import navigate_and_wait, scroll_to_bottom


ERROR_REASON_EMPTY_BODY = 'empty body'



async def wait_for_navigation(page: Page, result=None, navigation_tag: str = None):
    try:
        await page.wait_for_load_state('networkidle')
    except TimeoutError:
        if result is not None:
            result.warnings.append(f'{navigation_tag}Navigation timeout')


async def set_screenshot(page: Page, result, screenshot_name: str):
    """Get base64-encoded thumbnail of the screenshot."""
    try:
        img_bytes = await page.screenshot()
        setattr(result, screenshot_name, encode_to_base64(
            img_bytes, new_size=(800, 600)))
    except TimeoutError:
        result.warnings.append(
            f'Screenshot {screenshot_name} timeout')


async def set_perf_timing(page: Page, result):
    try:
        perf_timing_json = await asyncio.wait_for(page.evaluate('() => JSON.stringify(window.performance.timing)'), timeout=5)
        result.perf_timing = json.loads(perf_timing_json)
    except asyncio.TimeoutError:
        result.warnings.append(
            'Evaluate perf_timing script timeout.')


async def get_frame_content(frame: Frame, log=None, verbose=0):
    try:
        return await asyncio.wait_for(frame.content(), timeout=5)
    # except asyncio.TimeoutError:
    except Exception as e:
        msg = f"Get frame content error {frame.url=}: {e}"
        if verbose >= 2: print(msg)
        if log is not None:
            log.warnings.append(msg)
    return None


async def get_frames(page: Page, log, verbose=0):
    tasks = [asyncio.create_task(get_frame_content(frame, log)) for frame in page.frames]
    frame_contents = await asyncio.gather(*tasks)

    frames = []
    for frame, frame_content in zip(page.frames, frame_contents):
        if verbose >= 4:
            print(f'{frame.url=} {frame_content=}')
        if frame_content is not None:
            frames.append({
                'url': frame.url,
                'content': frame_content
            })
    return frames


class PageLoader(Scanner):
    def __init__(self, url: str, take_screenshot=1, nav_wait_sec=None, result=None):
        super().__init__()
        self._url = url
        self._take_screenshot = take_screenshot
        self._nav_wait_sec = nav_wait_sec
        self._result = PageLoadResult(
            initial_url=url) if result is None else result

    async def _run(self, page: Page, verbose=2):
        if verbose >= 2:
            print(f'Scan url {self._url}')

        await navigate_and_wait(page, self._url, result=self._result)

        # Extra wait for fully loading/displaying banners
        if self._nav_wait_sec is not None:
            await asyncio.sleep(self._nav_wait_sec)

        # Set the final (possibly redirected) url.
        self._result.url = page.url
        assert page.url == page.main_frame.url, f'{page.url=} {page.main_frame.url=}'

        # self._result.page_html = await page.content()
        self._result.frames = await get_frames(page, log=self._result)
        assert any(page.url in frame['url'] for frame in self._result.frames), f'{page.url=} not in frames'

        await set_perf_timing(page, result=self._result)
        if self._take_screenshot > 0:
            await set_screenshot(page, self._result, 'screenshot')

        # Scrolling down, may load more contents and cookies.
        await scroll_to_bottom(page)
        await asyncio.sleep(5)  # wait 5 sec for the page to render.

        if self._take_screenshot > 1:
            await set_screenshot(page, self._result, 'screenshot_bottom')

        self._result.cookies = await page.context.cookies()
