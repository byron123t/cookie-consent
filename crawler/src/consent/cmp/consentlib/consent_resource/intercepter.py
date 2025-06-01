from multiprocessing import Lock
from pathlib import Path
from typing import Dict, List
import json

from playwright.async_api import Page, Response

from consent.cmp.consentlib.consent_resource.factory import ConsentResourceFactory


class ConsentResourceIntercepter:
    def __init__(self, page: Page, out_file: Path):
        self._page = page
        self._resources: List[Dict[str, str]] = []
        self._out_file = out_file
        self._lock = Lock()

    async def __aenter__(self):
        self._page.on('response', self.intercept_resources)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        self._page.remove_listener('response', self.intercept_resources)
        # await self._page.close() # TODO: may try this?
        self._dump_to_json()

    @property
    def resources(self):
        self._lock.acquire()
        try:
            return self._resources
        finally:
            self._lock.release()

    async def intercept_resources(self, response: Response, verbose=2):
        if verbose >= 3: print("Intercept resources:", self._page.url, response.url)
        consent_resource_class = ConsentResourceFactory.get_class_from_url(self._page.url, response.url)
        if consent_resource_class is not None:
            if verbose >= 1: print(f"Intercept resources: found resources of {consent_resource_class.lib_name}")
            try:
                if self._lock.acquire(timeout=10):  # 10 secs timeout
                    self._resources.append({
                        'url': response.url,
                        'response': await response.text(),
                        'lib_name': consent_resource_class.lib_name,
                        'pattern_name': consent_resource_class.pattern_name,
                        'resource_type': consent_resource_class.resource_type
                    })
                else:
                    if verbose >= 2: print("intercept_resources: Cannot acquire lock")
            finally:
                self._lock.release()


    def _dump_to_json(self):
        self._out_file.write_text(json.dumps(self.resources))
