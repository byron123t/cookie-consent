from pathlib import Path
from typing import Any, List
import contextlib
import json

from playwright.async_api import Page

from consent.har.har import HAR
from consent.har.har_page import HarPage
from ooutil.compress.compress_json import dump
from ooutil.async_util import asyncio_wait_for_timeout

NETWORK_ENABLE_METHOD = "Network.enable"
PAGE_ENABLE_METHOD = "Page.enable"


class HarCapturer:
    async def from_page(self, page: Page, har_file: Path, init_methods: List[str]):
        self._har_file = har_file
        # Must set har page before listening because process_message access this property
        self._har_page = HarPage(0)
        self._page = page

        self._client = await page.context.new_cdp_session(page)
        self._orig_on_event_callback = self._client._impl_obj._on_event
        self._client._impl_obj._on_event = self._on_event

        for init_method in init_methods:
            await self._client.send(init_method)
        return self

        # await self._client.send("Debugger.enable") # Capture stacktrace.
        # await self._client.send("Page.enable") # Capture page load time.
        # await self._client.send("Network.enable") # Capture network events.
        # self._client.on("Network.requestWillBeSent", lambda e: print(f"{e=}"))
        # if method == 'Page.domContentEventFired':
        # elif method == 'Page.loadEventFired':
        # if method == 'Network.requestWillBeSent':
        #     elif method == 'Network.dataReceived':
        #     elif method == 'Network.responseReceived':
        #     elif method == 'Network.loadingFinished':

    def _on_event(self, message: Any) -> None:
        self._har_page.process_message(message)
        self._orig_on_event_callback(message)

    async def detach(self, verbose=2):
        if verbose >= 2: print("Detaching HAR capturer.")
        if self._client:
            success = await asyncio_wait_for_timeout(self._client.detach(), default_val=-1)
            if success == -1:
                msg = "Error detaching HAR"
                print(msg)
                raise ValueError(msg)
        return True

    def save(self, verbose=2):
        """Save to a HAR file."""
        if verbose >= 2: print("HAR capturer: saving...")
        self._har_page.url = self._page.url  # Set here to get the final URL.
        har = HAR()
        har.from_page(self._har_page)

        # Compression is inferred from file name.
        dump(har.har, str(self._har_file))
        if verbose >= 2: print("Dumped har file to ", self._har_file)
        # self._har_file.write_text(json.dumps(har.har, indent=4))

    async def detach_and_save(self):
        if await self.detach():
            self.save()

@contextlib.asynccontextmanager
async def get_har_capturer(page, out_har_file):
    har_capturer = await HarCapturer().from_page(
        page, out_har_file, [NETWORK_ENABLE_METHOD, PAGE_ENABLE_METHOD])
    try:
        yield har_capturer
    finally:
        await har_capturer.detach_and_save()