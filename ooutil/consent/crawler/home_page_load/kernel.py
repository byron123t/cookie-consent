"""Scan loading of the websites."""

from consent.crawler.home_page_load.result import HomePageLoadResult
from consent.data.database.exper_result_database import ExperResultRegistry
from ooutil.crawler.scanner import Scanner, ScannerRunner
from ooutil.crawler.page_load.kernel import PageLoader
from ooutil.url_util import get_home_page_urls_from_domain
from ooutil.crawler.error import Error, get_error_dict_from_exception


class HomePageLoader(Scanner):
    def __init__(self, website, location, take_screenshot=2):
        super().__init__()
        self._website = website
        self._take_screenshot = take_screenshot
        self._location = location
        self._nav_wait_sec = 20 if location == 'eu' else 10
        self._result = HomePageLoadResult(site=self._website, location=location)

    async def _scan_home_page_urls(self, page, verbose=2):
        if verbose >= 2: print(f'_scan_home_page_urls for website {self._website}')

        home_page_urls = list(get_home_page_urls_from_domain(self._website))
        if len(home_page_urls) == 0:
            raise ValueError('Cannot get home page urls from domain')
        assert all(url.startswith('http') for url in home_page_urls), f'{home_page_urls=} should start with http'

        result = None
        for home_page_url in home_page_urls:
            page_loader = PageLoader(home_page_url, take_screenshot=self._take_screenshot, nav_wait_sec=self._nav_wait_sec,
                                     result=HomePageLoadResult(site=self._website, initial_url=home_page_url, location=self._location))
            result = await page_loader.run(page)
            if result.error is None:
                break

        # If all home page URL loading fail, return the last one.
        return result

    # bypass scanner's run() wrapper because this class does not inherit but use PageLoader
    async def run(self, page):
        self._result = await self._scan_home_page_urls(page)
        return self._result


async def kernel(website, exper_date, proxy_url, location):
    proxy = {'server': proxy_url} if proxy_url else None
    print('Proxy url:', proxy_url)
    result = await ScannerRunner.run(HomePageLoader(website, location), proxy=proxy)
    try:
        ExperResultRegistry.save_result(result, exper_date)
    except Exception as e:
        result = HomePageLoadResult(site=website, location=location)
        result.error = Error.from_exception(e)
        print("Error saving, retry:", get_error_dict_from_exception(e))
        ExperResultRegistry.save_result(result, exper_date)
