""" Experimental detection. """

from playwright.async_api import Page

from ooutil.browser_control import page_contains

lib_to_sel = {
    "onetrust": "#onetrust-pc-sdk, #onetrust-consent-sdk",
    "onetrust_legacy": "#optanon-popup-wrapper",
    "trustarc": '#truste-consent-content, .truste-consent-content',
    "quantcast": "#qc-cmp2-container",
    'quantcast_legacy': ".qc-cmp-ui-container",
    "cookiebot": "#CybotCookiebotDialog, #CybotCookiebotDialogBodyLevelButtonPreferences",
    "osano": ".osano-cm-window",
    "google": '[onclick*="googlefc.showRevocationMessage()"]',
    "ensighten": ".ensModalWrapper",
    "sourcepoint": '#sp_privacy_manager_container, iframe[src*="https://cdn.privacy-mgmt.com"]'
}


async def detect_consent_lib_on_page(page: Page):
    for lib, selector in lib_to_sel.items():
        if await page_contains(page, selector):
            print("Page contain consent library:", lib)
            return lib
    return None


def detect_consent_lib_on_soup(soup):
    for lib, sel in lib_to_sel.items():
        found = soup.select_one(sel)
        if found is not None:
            return lib
    return None
