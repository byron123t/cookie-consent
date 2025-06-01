"""Auto-reject cookie consent on a website."""

from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin
import asyncio
import json
import random

from playwright.async_api import Page
from consent.cmp.consentlib.consent_lib import ConsentLib
from consent.cmp.consentlib.detector import get_consent_lib
from consent.cmp.consentlib.consent_resource.intercepter import ConsentResourceIntercepter
from consent.crawler.consent_scan.log import ConsentScannerLog
from consent.crawler.consent_scan.result import FramesLog
from consent.har.page_util import goto_and_dump_cookies_har
from ooutil.crawler.scanner import ScannerFile, ScannerRunner
from ooutil.crawler.page_load.kernel import get_frames
from ooutil.cookie_util import url_domain_match
from ooutil.url_util import is_pdf, is_absolute
from ooutil.browser_control import take_screenshot_ignore_timeout
from consent.cmp.consentlib.termly import get_termly_consent_state


CONSENT_LIB_NOT_FOUND = 'consent_lib_not_found'

async def dump_consent_state(page: Page, out_file: Path, verbose=2):
    # TODO: avoid hard code Termly if there is another library using local storage.
    consent_state = await get_termly_consent_state(page)

    out_file.write_text(json.dumps(consent_state, indent=4))
    if verbose >= 2: print(f'Writtent {consent_state=} to {out_file=}')


async def sample_subpages(page: Page, domain: str, max_subpages=None, verbose=2):
    if verbose >= 2:
        print('Sample subpages')

    subpages = set()
    page_url = page.url

    for a_elem in await page.query_selector_all('a'):
        href = await a_elem.get_attribute('href')
        if verbose >= 3:
            print(f"{href=}")

        if href is not None and len(href) > 0 and not href.startswith('#'):
            # If href is absolute or relative absolute, or mailto, urljoin will use it.
            href = urljoin(page_url, href)
            # Only use absolute url; Only go to same domain; do not go to the home page; avoid pdf files (very common)
            if is_absolute(href) and url_domain_match(href, domain) and page_url != href and not is_pdf(href):
                subpages.add(href)

    if max_subpages is not None:
        subpages = set(random.sample(
            subpages, min(len(subpages), max_subpages)))

    if verbose >= 3:
        print(f"{subpages=}")
    return subpages


async def visit_dump_screenshot(apage: Page, aurl: str, har_file: Path, cookie_file: Path, consent_state_file: Optional[Path] = None, screenshot_file: Path = None, warnings: List = None, verbose=2):
    assert cookie_file.suffix == '.json' and (
        screenshot_file is None or screenshot_file.suffix == '.png')
    try:
        await goto_and_dump_cookies_har(apage, aurl, har_file, cookie_file)
        if consent_state_file is not None:
            await dump_consent_state(apage, consent_state_file)
        if screenshot_file is not None:
            # await apage.screenshot(path=screenshot_file)
            await take_screenshot_ignore_timeout(apage, path=screenshot_file)
        return True
    except Exception as e:
        msg = f"Go to {aurl} fail with error {e}"
        if warnings is not None:
            warnings.append(msg)
        if verbose >= 2: print(msg)
    return False

async def visit_dump_screenshot_close(apage: Page, aurl: str, har_file: Path, cookie_file: Path, consent_state_file: Optional[Path], screenshot_file: Path = None, warnings: List = None):
    if await visit_dump_screenshot(apage, aurl, har_file, cookie_file, consent_state_file, screenshot_file, warnings):
        await apage.close()

class ConsentScanner(ScannerFile):
    def __init__(self, site: str, url: str, consent: bool, out_dir: Path, proxy_url: str, location: str):
        super().__init__(out_dir)
        self._site = site
        self._url = url
        self._log: ConsentScannerLog = ConsentScannerLog()
        self._consent = consent
        self._consent_lib: Optional[ConsentLib] = None
        self._log.scan_result['proxy_url'] = proxy_url
        self._log.scan_result['location'] = location

    async def _goto_and_dump_cookies_on_home_page(self, page: Page):
        # Scroll-to-bottom will be done in the consentlib.detector only when necessary to avoid "consent on scroll" that hide initial cookie banners.
        await goto_and_dump_cookies_har(page, self._url, self._out_dir / 'prerej.har.xz', self._out_dir / 'prerej_cookies.json', do_scroll_to_bottom=False)
        # await page.screenshot(path=self._out_dir / 'prerej_page.png')
        await take_screenshot_ignore_timeout(page, path=self._out_dir / 'prerej_page.png')

    async def _dump_frames(self, page: Page, out_file: Path):
        # Record frames when the menu is opened.
        frames_log = FramesLog(main_frame_url=page.url)
        frames = await get_frames(page, log=frames_log)
        assert any(page.url in frame['url']
                   for frame in frames), f'{page.url=} not in frames'
        frames_log.frames = frames
        out_file.write_text(frames_log.to_json())

    async def _dump_cookies_on_subpages(self, page: Page, out_dir: Path, n_subpages: int, warnings: List):
        """Dump cookies of the refreshed home page. Go to (5) random sub-pages and dump {url: url, sent_cookies, browser cookie}"""
        brcontext = page.context
        assert self._consent_lib is not None, CONSENT_LIB_NOT_FOUND

        # Visit home page and subpages on new tabs. Opening sequentially seems the same with the async way.
        tasks = []
        for i, sub_url in enumerate(await sample_subpages(page, await self._consent_lib.get_effective_domain(), n_subpages), 1):
            tasks.append(asyncio.create_task(visit_dump_screenshot_close(
                apage=await brcontext.new_page(),
                aurl=sub_url,
                har_file=out_dir / f'postrej_{i}.har.xz',
                cookie_file=out_dir / f'postrej_{i}_cookies.json',
                consent_state_file=(out_dir / f'postrej_{i}_consent_state.json') if self._should_dump_consent_state() else None,
                screenshot_file=out_dir / f'postrej_{i}_subpage.png',
                warnings=warnings # race condition may not exist because we use asyncio & append is atomic bit.ly/3GWXjs6
            )))
            # await visit_dump_screenshot(apage, sub_url, har_file, cookie_file, screenshot_file, warnings)
            # await apage.close()

        await asyncio.gather(*tasks)

    async def _detect_and_set_consent(self, page: Page):
        self._consent_lib = await get_consent_lib(page, self._out_dir / 'prerej_pref_menu.png', self._log.warnings)
        if self._consent_lib is None:
            raise ValueError(CONSENT_LIB_NOT_FOUND)

        self._log.scan_result['consent_lib_name'] = self._consent_lib.name
        await self._dump_frames(page, out_file=self._out_dir / 'pref_menu_frames.json')

        await self._consent_lib.set_consent(self._consent, self._log.scan_result, self._out_dir / 'postrej_pref_menu.png', self._out_dir / f'postrej_browser_cookies.json', self._log.warnings)

    def _should_dump_consent_state(self):
        return self._consent_lib.name in ['termly']

    async def _may_dump_consent_state(self, page, out_file):
        if self._should_dump_consent_state():
            await dump_consent_state(page, out_file)

    async def _run(self, page: Page):
        """3 steps: 1. dump pre-reject cookie, 2. reject and collect cookie cats, 3. dump post-reject cookies on random subpages."""
        async with ConsentResourceIntercepter(page, self._out_dir / 'consent_resources.json'):
            await self._goto_and_dump_cookies_on_home_page(page)
            await self._dump_frames(page, out_file=self._out_dir / 'page_load_frames.json')

            await self._detect_and_set_consent(page)
            await self._may_dump_consent_state(page, self._out_dir / 'prerej_consent_state.json')

        # Reload the home page to get a new page in case the old page changed due to navigation of pref btn clicking.
        page = await page.context.new_page()
        await goto_and_dump_cookies_har(page, self._url, self._out_dir / f'postrej_0.har.xz', self._out_dir / f'postrej_0_cookies.json')
        await self._may_dump_consent_state(page, self._out_dir / 'postrej_0_consent_state.json')

        await self._dump_cookies_on_subpages(page, self._out_dir, n_subpages=5, warnings=self._log.warnings)


def clear_dir(out_dir: Path):
    """Remove data files, safer than shutil.rmtree."""
    for afile in out_dir.glob('*'):
        if afile.suffix in ['.json', '.png', '.xz', '.har']:
            afile.unlink()

# consent paremeter means to given consent to the cookie banner or not.
async def kernel(exper_date: str, site: str, url: str, consent: bool, overwrite: bool, proxy_url: str, location: str):
    # Create output directory.
    out_dir: Path = Path.cwd() / "crawl_results" / exper_date / site
    if overwrite and out_dir.exists():
        clear_dir(out_dir)
    out_dir.mkdir(exist_ok=True, parents=True)
    print(f'Proxy url: {proxy_url}')
    print(f'Output dir: {out_dir}')

    # # Write results into the output dir.
    scanner = ConsentScanner(site, url, consent, out_dir, proxy_url, location)
    await ScannerRunner.run(scanner, proxy={'server': proxy_url} if proxy_url else None, headless=True)
    scanner.dump_log()
