"""Generic runner for page-loader."""

from pathlib import Path
from ooutil.json_util import dump_to_json_file

from playwright.async_api import Page

from ooutil.browser_factory import get_page
from ooutil.crawler.error import Error, get_error_dict_from_exception
from ooutil.crawler.log import Log
from ooutil.crawler.result import DefaultResult


class Scanner:
    def __init__(self):
        self._result = DefaultResult()

    @property
    def result(self):
        return self._result

    async def run(self, page):
        try:
            await self._run(page)
            assert self._result is not None, "self._result should not be None after self.run()"
        except Exception as e:
            if self._result is None:
                self._result = DefaultResult()

            self._result.error = Error.from_exception(e)
        return self._result

    async def _run(self, page: Page):
        raise NotImplementedError


class ScannerFile(Scanner):
    """Scanner and record data to files."""
    def __init__(self, out_dir: Path):
        self._log: Log = Log()
        self._out_dir = out_dir

    def dump_log(self):
        log_file = self._out_dir / 'log.json'
        log_file.write_text(self._log.to_json())
        print(f"Written log to {log_file}")

    async def run(self, page: Page, verbose=2):
        try:
            await self._run(page)
        except Exception as e:
            self._log.error = get_error_dict_from_exception(e)

        if verbose >= 2:
            if hasattr(self._log, 'error') and self._log.error:
                print(self._log.error)

            if verbose >= 3 and hasattr(self._log, 'warnings') and self._log.warnings:
                print(self._log.warnings)

        self.dump_log()


class ScannerRunner:
    @classmethod
    async def run(cls, scanner: Scanner, proxy=None, headless=True):
        async with get_page(headless=headless, stealth_mode=True, proxy=proxy) as page:
            return await scanner.run(page)
