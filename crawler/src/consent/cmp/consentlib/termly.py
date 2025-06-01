import asyncio
import json
from typing import Dict, List, Type

from playwright.async_api import Page

from consent.cmp.consentlib.consent_cookie import ConsentCookie
from consent.cmp.consentlib.consent_lib import ConsentLib
from consent.cmp.consentlib.cookie_consent import CategoryConsent, CookieConsent
from ooutil.browser_control import try_click, get_local_storage_key
from ooutil.url_util import get_suffixed_domain_with_dot_prefix
from ooutil.crawler.error import get_error_dict_from_exception


async def get_termly_consent_state(page: Page) -> Dict:
    try:
        return await page.evaluate('Termly.getConsentState()')
    except Exception as e:
        print('Error getting termly consent state:', get_error_dict_from_exception(e))
    return {}


# TODO: support local storage separately instead of emulating a cookie
class TermlyApiCacheLocalStorage(ConsentCookie):
    local_storage_key = 'TERMLY_API_CACHE'

    def __init__(self, kv_map, domain):
        emulate_cookie = {'name': self.local_storage_key, 'domain': domain, 'path': '/'}
        super().__init__(emulate_cookie)
        self.kv_map = kv_map
        # print(f'\n{self.kv_map=}')

    def get_val(self, key: str):
        return self.kv_map.get(key)

    def get_characteristic_val(self):
        return self.kv_map.get('RANDOM_UUID', {}).get('value', '') # these are commonly different

    def get_cat_to_pref(self, verbose=0):
        cookie_consent = self.kv_map.get('TERMLY_COOKIE_CONSENT', {})
        if verbose >= 2: print(f'{cookie_consent=}')

        cookie_consent_val = cookie_consent.get('value', {})
        if verbose >= 2: print(f'{cookie_consent_val=}')

        return {cat: cookie_consent_val.get(cat, False) for cat in TermlyConsentLib.get_cookie_categories()}


class TermlyConsentLib(ConsentLib):
    name = 'termly'
    consent_cookie_cls: Type[TermlyApiCacheLocalStorage] = TermlyApiCacheLocalStorage
    pref_save_btn_sels = ['button.t-saveButton']
    pref_menu_sels = ['div.t-preference-modal']

    @classmethod
    def get_cookie_categories(cls):
        return ['essential', 'performance', 'analytics', 'advertising', 'social_networking', 'unclassified']

    @classmethod
    def get_cat_to_sels(cls):
        return {cat: [f'label.t-checkBox--{cat}'] for cat in cls.get_cookie_categories()}

    async def open_cookie_settings(self):
        pref_btn_sel = self.pref_menu_sels[0]
        pref_btn = await self._page.wait_for_selector(pref_btn_sel)
        if not await try_click(pref_btn):
            raise ValueError(f"Cannot click on pref menu button {pref_btn_sel=}")

    async def _set_consent_preferences(self, consent: bool, scan_result: Dict, verbose=2) -> CookieConsent:
        if not consent:
            deny_all_btn = await self._pref_menu_el.wait_for_selector('button.t-declineAllButton')
            await try_click(deny_all_btn)
        else:
            allow_all_btn = await self._pref_menu_el.wait_for_selector('button.t-allowAllButton')
            await try_click(allow_all_btn)

        self._do_save_pref = False # we click on deny/allow all -> do not do saving afterward.

        cookie_consent = CookieConsent()
        for cookie_cate in self.get_cookie_categories():
            if verbose >= 2: print(f"Set pref on {cookie_cate} ...")

            # TODO: check the input of the label on the UI. This might be hard because of the scrolling?
            # Assume deny-all => None -> False, allow-all => None -> True
            if consent or cookie_cate == 'essential':
                cur_status = True
            else:
                cur_status = False

            cookie_consent[cookie_cate] = CategoryConsent(
                category=cookie_cate,
                category_id=cookie_cate,
                prev_status=None,
                cur_status=cur_status,
            )

        return cookie_consent

    # @override
    async def _find_consent_cookie(self, warnings: List=None, verbose=0):
        termly_local_storage = await get_local_storage_key(self._page, self.consent_cookie_cls.local_storage_key, get_json_dict=True)
        if verbose >= 3:
            print(f'{termly_local_storage=}')

        # Assume the domain is the domain of the current page
        domain = get_suffixed_domain_with_dot_prefix(self._page.url)
        self._consent_cookie = self.consent_cookie_cls(termly_local_storage, domain=domain)
