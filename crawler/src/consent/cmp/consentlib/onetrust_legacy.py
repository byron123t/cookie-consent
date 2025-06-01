from consent.cmp.consentlib.consent_lib import ConsentLib

class OneTrustLegacyConsentLib(ConsentLib):
    name = 'onetrust_legacy'
    # consent_cookie_cls = OptanonConsentCookie
    pref_save_btn_sels = ['button.save-preference-btn-handler']
    pref_menu_sels = ['#optanon-popup-wrapper']
    pass

# async def contain_legacy_pref_menu(page: Page):
#     try:
#         await page.wait_for_selector("#optanon-popup-wrapper", timeout=5000)
#         return True
#     except TimeoutError:
#         pass
#     return False


# async def get_consent_lib(page: Page) -> Union[ConsentLib, None]:
#     try:
#         pref_menu_el = await page.wait_for_selector(, timeout=5000)
#         return OneTrustConsentLib(page, pref_menu_el)
#     except TimeoutError:
#         pass

#     # if await contain_legacy_pref_menu(page):
#         # raise ValueError('onetrust_legacy')

#     return None