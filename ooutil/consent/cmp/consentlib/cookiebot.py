"""Support to analyze cookie bot."""

from typing import Dict, List
from urllib.parse import unquote
from io import BytesIO
from IPython.display import display
from PIL import Image
import asyncio
import json5

from ooutil.async_util import asyncio_wait_for_timeout
from consent.cmp.consentlib.consent_lib import ConsentLib
from consent.cmp.consentlib.cookie_consent import CategoryConsent, CookieConsent
from consent.cmp.consentlib.consent_cookie import ConsentCookie, CONSENT_COOKIE_DECODE_ERROR
from ooutil.browser_control import is_input_checked, try_click, try_get_one_element

# From uc.js and CookieConsent cookie
consent_categories = ['necessary', 'preferences', 'statistics', 'marketing']

class CookiebotConsentCookie(ConsentCookie):
    consent_cookie_name = 'CookieConsent'

    def __init__(self, cookie: Dict[str, str]):
        super().__init__(cookie)
        assert self._cookie['name'] == self.consent_cookie_name, f"{self._cookie=}"
        self.kv_map = self.decode_value(self._cookie['value'])

    def get_val(self, key: str):
        return self.kv_map.get(key)

    def get_characteristic_val(self):
        return self.kv_map.get('stamp', '')

    def get_cat_pref_str(self):
        sep = '%2C'
        cat_pref_strs = []
        cat_to_pref = self.get_cat_to_pref()
        for cat in consent_categories:
            pref = 'true' if cat_to_pref[cat] else 'false'
            cat_pref_strs.append(f'{cat}:{pref}')
        return sep.join(cat_pref_strs)

    def decode_value(self, cookie_val: str):
        consent_dict = json5.loads(unquote(cookie_val))
        try:
            cat_to_pref = {k: consent_dict[k] for k in consent_categories}
            assert 'unclassified' not in cat_to_pref, f'{CONSENT_COOKIE_DECODE_ERROR} unclassified should not in the cookie {consent_dict=}'
        except Exception as e:
            raise ValueError(f"{CONSENT_COOKIE_DECODE_ERROR} Cannot decode cookie value {cookie_val=} {e}")
        return cat_to_pref

    def get_cat_to_pref(self):
        cat_to_pref = self.kv_map.copy()
        assert 'unclassified' not in cat_to_pref, f'{CONSENT_COOKIE_DECODE_ERROR} unclassified should not in the cookie {cat_to_pref=}, copy not working?'
        cat_to_pref['unclassified'] = True
        return cat_to_pref


class CookiebotConsentLib(ConsentLib):
    cat_to_sels: Dict[str, List[str]] = {}
    detail_btn_sels: List[str] = []
    name = 'cookiebot'
    consent_cookie_cls = CookiebotConsentCookie

    async def _check_necessary_cat(self, necessary_btn, scan_result):
        disabled = await asyncio_wait_for_timeout(necessary_btn.get_attribute('disabled'))
        if disabled != 'disabled': #  and checked:# should be disabled
            scan_result.warnings.append(f'Unexpected necessary cookie preferences: {disabled=}')

    async def _set_consent_preferences(self, consent: bool, scan_result: Dict, verbose=2):
        # Try to get visible first, if not, retry to get the buttons attached.
        show_details_btn = await try_get_one_element(self._page, self.detail_btn_sels, state='visible', timeout=5000)
        if show_details_btn is None:
            show_details_btn = await try_get_one_element(self._page, self.detail_btn_sels, state='attached', timeout=5000)
            if show_details_btn is None:
                raise ValueError("Cannot find Show Details button")

        if not await try_click(show_details_btn):
            raise ValueError("Cannot click on show details btn.")

        if verbose >= 2: print("Clicked on show details btn.")
        if verbose >= 4: await asyncio.sleep(1); display(Image.open(BytesIO(await self._page.screenshot())))

        cookie_consent = CookieConsent()
        for cat, btn_sels in self.cat_to_sels.items():
            if verbose >= 2: print(f"Set pref on {cat} ...")
            # Do not check the visibilty here because the click will check and may scroll to the button.
            cat_select_btn = await try_get_one_element(self._page, btn_sels, state='attached', timeout=5000)
            if cat_select_btn is None:
                raise ValueError(f"Cannot get button for category {cat}")

            consented = await is_input_checked(cat_select_btn)

            disabled = await asyncio_wait_for_timeout(cat_select_btn.get_attribute('disabled'))
            if disabled != 'disabled' and consent != consented:  # may be disabled if cat == 'necessary':
                if not await try_click(cat_select_btn):
                    raise ValueError(f"Cannot change status for category {cat}")
                if verbose >= 2: print(f'Changed status for category {cat}')
                if verbose >= 4: await asyncio.sleep(1); display(Image.open(BytesIO(await self._page.screenshot())))

            cat_consent = CategoryConsent(
                category=cat,
                category_id=cat,
                prev_status=consented,
                cur_status=await is_input_checked(cat_select_btn),
                # cookie_list=[]
            )
            if verbose >= 2: print(f'{str(cat_consent)=}')
            cookie_consent[cat] = cat_consent
        return cookie_consent

class CookiebotLegacyConsentLib(CookiebotConsentLib):
    # See https://github.com/cavi-au/Consent-O-Matic/blob/master/Rules.json#L2063
    # Cookiebot JS interface: https://www.cookiebot.com/en/developer/

    name = 'cookiebot_legacy'
    pref_save_btn_sels = ['#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection', '#CybotCookiebotDialogBodyButtonAccept']
    pref_menu_sels = ['#CybotCookiebotDialog > #CybotCookiebotDialogBody']  # Need a stricter selector to distinguish with the new version.
    consent_cookie_cls = CookiebotConsentCookie

    cat_to_sels = {
        'necessary': ['#CybotCookiebotDialogBodyLevelButtonNecessary'],
        'preferences': ['#CybotCookiebotDialogBodyLevelButtonPreferences'],
        'statistics': ['#CybotCookiebotDialogBodyLevelButtonStatistics'],
        'marketing': ['#CybotCookiebotDialogBodyLevelButtonMarketing']
    }

    detail_btn_sels = ['#CybotCookiebotDialogBodyLevelDetailsButton']


class CookiebotNewConsentLib(CookiebotLegacyConsentLib):
    name = 'cookiebot_new'
    pref_menu_sels = ['#CybotCookiebotDialog > div.CybotCookiebotDialogContentWrapper']

    # Note: These are the selectors when activating detail view by clicking the "Show Details" button.
    # The selectors before clicking the button is the same with the Legacy version.
    cat_to_sels = {
        'necessary': ['#CybotCookiebotDialogBodyLevelButtonNecessaryInline'],
        'preferences': ['#CybotCookiebotDialogBodyLevelButtonPreferencesInline'],
        'statistics': ['#CybotCookiebotDialogBodyLevelButtonStatisticsInline'],
        'marketing': ['#CybotCookiebotDialogBodyLevelButtonMarketingInline']
    }

    detail_btn_sels = ['CybotCookiebotDialogBodyEdgeMoreDetailsLink', '#CybotCookiebotDialogBodyLevelButtonCustomize', '#CybotCookiebotDialogNavDetails']


assert set(CookiebotLegacyConsentLib.cat_to_sels.keys()) == set(consent_categories), f'Cookiebot class contains some invalid cookie categories.'
