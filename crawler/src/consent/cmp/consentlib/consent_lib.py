from pathlib import Path
from typing import Dict, List, Optional, Type
import asyncio

from colorama import Fore
from playwright.async_api import ElementHandle, Page, TimeoutError

from consent.cmp.consentlib.cookie_consent import CookieConsent
from consent.cmp.consentlib.consent_cookie import ConsentCookie
from ooutil.async_util import asyncio_wait_for_timeout
from ooutil.browser_control import try_click
from ooutil.cookie_store import CookieStore
from ooutil.json_util import dump_to_json_file


def match_consent_to_cookie(category_consent: Dict, cat_to_pref: Dict):
    # Some keys in cookie not in UI so check keys on UI only.
    for k, v in category_consent.items():
        if cat_to_pref[k] != v['cur_status']:
            raise ValueError(f"{k=} {cat_to_pref[k]=} != {v['cur_status']=} {category_consent=} {cat_to_pref=}")
    return True

def find_cookie_in_page_cookies(page_cookies: List, page_url: str, cookie_name_to_find: str, warnings=None) -> Optional[Dict[str, str]]:
    found_cookies = CookieStore(page_cookies, page_url).find_cookies_in_page(cookie_name_to_find)

    if len(found_cookies) > 1:
        if warnings: warnings.append(f'WARNING: Found multiple consent preference cookie {found_cookies=}')
    if len(found_cookies) == 0:
        return None
    return found_cookies.iloc[0].to_dict()


class ConsentLib:
    name = ''
    consent_cookie_cls: Type[ConsentCookie] = ConsentCookie
    pref_save_btn_sels: List[str] = []
    pref_menu_sels: List[str] = []

    def __init__(self, page: Page, pref_menu_el: ElementHandle, postrej_menu_screenshot_file: Path = None, extract_cookie_list: bool = False):
        self._page = page
        self._pref_menu_el = pref_menu_el
        self._postrej_menu_screenshot_file = postrej_menu_screenshot_file
        self._extract_cookie_list = extract_cookie_list  # Extract cookie list on UI
        self._consent_cookie: Optional[ConsentCookie] = None
        self._do_save_pref = True  # Perform saving after setting prefs by default, sometimes bypass this when we click "deny all" instead.

    async def get_effective_domain(self):
        return self._consent_cookie.domain

    async def _set_consent_preferences(self, consent: bool, scan_result: Dict) -> CookieConsent:
        raise NotImplementedError

    @classmethod
    async def try_to_create(cls, page: Page, verbose=2) -> Optional['ConsentLib']:
        for pref_menu_sel in cls.pref_menu_sels:
            try:
                pref_menu_el = await asyncio_wait_for_timeout(page.wait_for_selector(pref_menu_sel, timeout=5000), timeout=6, default_val=None)
                if pref_menu_el is not None:
                    if verbose >= 2: print(Fore.GREEN + f'[{cls.name}] found {pref_menu_sel}' + Fore.RESET)
                    return cls(page, pref_menu_el)
            except TimeoutError:
                pass
        if verbose >= 2: print(f'[{cls.name}] cannot find {cls.pref_menu_sels}')
        return None

    async def _get_pref_save_btn(self):
        try:
            for pref_save_btn_sel in self.pref_save_btn_sels:
                pref_btn = await self._page.wait_for_selector(pref_save_btn_sel, state='attached', timeout=5000)
                if pref_btn is not None:
                    return pref_btn
        except TimeoutError:
            pass
        return None

    async def _save_pref(self, verbose=2):
        pref_save_btn = await self._get_pref_save_btn()
        if pref_save_btn is None:
            raise ValueError("Cannot get pref save btn")

        clicked = await try_click(pref_save_btn)
        if not clicked:
            raise ValueError("Cannot click on pref save btn.")
        if verbose >= 2: print("Clicked on save pref btn.", pref_save_btn)

    async def _verify_consent_pref_cookie(self, category_consent: CookieConsent, verbose=2):
        if self._consent_cookie is None:
            raise ValueError("Consent cookie is not initialized")

        try:
            cat_to_pref = self._consent_cookie.get_cat_to_pref()
        except Exception as e:
            raise ValueError(f"Error getting cat-to-pref {e}: {self._consent_cookie.cookie=}")

        match_consent_to_cookie(category_consent, cat_to_pref)

        if verbose >= 2: print("Test cookie consent passed.")
        return True

    async def _find_consent_cookie(self, warnings: List=None, verbose=2):
        found_cookie = find_cookie_in_page_cookies(await self._page.context.cookies(), self._page.url, self.consent_cookie_cls.consent_cookie_name, warnings)
        if found_cookie is None:
            raise ValueError(f"Error: Cannot find {self.consent_cookie_cls.consent_cookie_name} cookie.")
        if verbose >= 2: print("Found consent cookie:", found_cookie)
        self._consent_cookie = self.consent_cookie_cls(found_cookie)

    async def set_consent(self, consent: bool, scan_result: Dict, postrej_menu_screenshot_file: Path = None, postrej_browser_cookies_file: Path = None, warnings: List=None, verbose=2):
        """scan_result: defaultdict(list)
        Consent map contains: cookie_category -> Dict as follows.
        {cookie_cat: {name, status (true, false, unavail, always-active), cookie list: a-list-of-cookies}
        """
        if verbose >= 2: print(f"Set consent to {consent}")
        cookie_consent = await self._set_consent_preferences(consent, scan_result)
        scan_result['category_consent'] = cookie_consent

        if postrej_menu_screenshot_file is not None:
            await self._page.screenshot(path=postrej_menu_screenshot_file)

        if self._do_save_pref:
            await self._save_pref()

        await asyncio.sleep(5) # wait for the pref to be saved.

        if postrej_browser_cookies_file:
            dump_to_json_file({'url': self._page.url, 'browser_cookies': await self._page.context.cookies()}, postrej_browser_cookies_file)

        await self._find_consent_cookie(warnings)
        await self._verify_consent_pref_cookie(cookie_consent)
