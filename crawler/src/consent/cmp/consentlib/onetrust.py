from pathlib import Path
from typing import Dict, List, Optional, Union
import asyncio
import urllib.parse

from playwright.async_api import ElementHandle, Page, TimeoutError

from consent.cmp.consentlib.consent_lib import ConsentLib
from consent.cmp.consentlib.cookie_consent import CategoryConsent, CookieConsent
from consent.cmp.consentlib.consent_cookie import ConsentCookie
from consent.cmp.consentlib.onetrust_cookie_list_extract import extract_cookie_list
from ooutil.async_util import asyncio_wait_for_timeout
from ooutil.browser_control import try_click, try_get_attribute


class OptanonConsentCookie(ConsentCookie):
    consent_cookie_name = 'OptanonConsent'

    def __init__(self, cookie: Dict):
        super().__init__(cookie)
        self.kv_map = self.decode_value(cookie['value'])

    @classmethod
    def decode_value(cls, cookie_val):
        return dict(kv.split('=', 1) for kv in cookie_val.split('&'))

    def get_val(self, key: str):
        return self.kv_map.get(key)

    def get_characteristic_val(self):
        return self.kv_map.get('version', '') # these are commonly different

    def get_cat_to_pref(self):
        groups_val = self.kv_map.get('groups')
        if groups_val is None:
            raise ValueError(f'Invalid cat-to-pref map {self.kv_map}')

        groups = urllib.parse.unquote(groups_val).split(',')
        group_map = {}
        for g in groups:
            k, v = g.split(':', 1)
            assert v in ['0', '1'], f'{v=} unsupported'
            group_map[k] = (v == '1')
        return group_map


async def get_menu_type(pref_menu_el: ElementHandle) -> str:
    pref_menu_class = await pref_menu_el.get_attribute('class')
    if pref_menu_class is not None:
        classes = set(pref_menu_class.split(' '))
        if len({'otPcCenter', 'otPcPanel', 'ot-accordions-pc'}.intersection(classes)) > 0:
            return 'accordion'
        elif len({'otPcTab', 'otPcPanel'}.intersection(classes)) > 0:
            return 'tab'
    raise ValueError("Cannot detect menu type!")


def convert_status_to_bool(status):
    # return status in ['true', 'unavailable']
    return status != 'false'


class OneTrustConsentLib(ConsentLib):
    name = 'onetrust'
    consent_cookie_cls = OptanonConsentCookie
    pref_save_btn_sels = ['button.save-preference-btn-handler']
    pref_menu_sels = ['#onetrust-pc-sdk']

    async def _set_consent_preferences(self, consent: bool, scan_result: Dict, verbose=2):
        try:
            pref_menu_type = await get_menu_type(self._pref_menu_el)
        except ValueError as e:
            print("Does not support pref menu type", e)
            return {}
        if verbose >= 2: print(f'{pref_menu_type=}')
        scan_result['pref_menu_type'] = pref_menu_type

        cat_group_sel = '.ot-cat-grp, .category-group'
        # this is not visble
        cat_group_el = await self._pref_menu_el.wait_for_selector(cat_group_sel, timeout=5000, state='attached')
        if cat_group_el is None:
            raise ValueError('Cannot find category group element')

        cat_item_sel = '.ot-cat-item, .category-item'
        always_active_sel = '.ot-always-active, .always-active'  # [variant]
        # toggle_el_sel = '.ot-tgl, .ot-tgl-cntr, .toggle-group, .ot-toggle' #[variant]  # toggle-group contains always-active

        cookie_consent = CookieConsent()
        tab_desc_el = None
        for cat_item_el in await cat_group_el.query_selector_all(cat_item_sel):
            optanon_group_id = await try_get_attribute(cat_item_el, 'data-optanongroupid', "Cannot get optanon group id")
            if verbose >= 2: print(f'{optanon_group_id=}')

            category_name = None
            if pref_menu_type == 'tab':
                # print(f'Try: {await cat_item_el.inner_html()}')
                cat_switch_el = await cat_item_el.wait_for_selector(".category-menu-switch-handler", state='attached', timeout=5000)
                # if not await cat_switch_el.is_visible():
                #     print(f'Category switch element is not visible')
                #     continue

                if cat_switch_el is None:
                    raise ValueError("Cannot find category switch element")

                category_name = await cat_switch_el.text_content()

                # await cat_switch_el.click()
                # playwright click timeout
                await cat_switch_el.evaluate_handle('e => e.click()')
                await asyncio.sleep(1)
                tab_desc_el = await asyncio_wait_for_timeout(self._pref_menu_el.wait_for_selector(f'#ot-desc-id-{optanon_group_id}'), timeout=3000, default_val=None)
            elif pref_menu_type == 'accordion':
                cat_header = await cat_item_el.wait_for_selector(f'#ot-header-id-{optanon_group_id}', state='attached', timeout=5000)

                try:
                    # await cat_item_el.click(timeout=5000)
                    await try_click(cat_item_el)
                    if verbose >= 2: print("Clicked on category header")
                except TimeoutError:
                    print("Cannot clicked on the category header (possible hidden category like foodandwine.com), continue")

                if cat_header is None:
                    raise ValueError("Cannot get category header")

                category_name = await cat_header.text_content()
                tab_desc_el = cat_item_el

            if category_name is None:
                raise ValueError("Cannot get category name")
            category_name = category_name.strip()
            print(f'Category name: {category_name}')

            el_choice_input = None
            try:
                # togl_el = await pref_menu_el.wait_for_selector(toggle_el_sel, timeout=5000)
                el_choice_input = await self._pref_menu_el.wait_for_selector(f'#ot-group-id-{optanon_group_id}', state='attached', timeout=5000)
            except TimeoutError:
                pass

            def get_status_string(status):
                if status is None: return 'false'
                if status == True: return 'true'
                if status == False: return 'false'
                return status

            async def get_element_status(el):
                # thomsonreuters.net
                status = await el.get_attribute('aria-checked')
                if status is not None:
                    return get_status_string(status)

                # simonandschuster.com
                status = await el.get_attribute('checked')
                if status is not None:
                    return get_status_string(status)

                # Use is_checked().
                return get_status_string(await el.is_checked())

            # default is to reject, so is 'true'
            status_to_set = 'true' if consent else 'false'
            if verbose >= 2: print('Status to set:', status_to_set)
            if el_choice_input is not None and not (await el_choice_input.get_attribute('aria-hidden')):
                if verbose >= 2: print("Choice input element:", el_choice_input)
                prev_status = await get_element_status(el_choice_input)
                print('Current choice status:', prev_status)
                # Reject when consent is true
                if prev_status != status_to_set:
                    # playwrigh cannot click on this 0-dimension button
                    await el_choice_input.evaluate_handle('e => e.click()')
                    await asyncio.sleep(1)  # wait for change of toggle?
                    cur_status = await get_element_status(el_choice_input)
                    print('-> After-reject status:', cur_status)
                    assert cur_status != prev_status, f"{cur_status=} is the same with current status, no effect button?"
                else:
                    cur_status = prev_status  # does nothing
            else:
                prev_status = 'unavailable'
                if 'ot-always-active-group' not in await try_get_attribute(cat_item_el, 'class'):
                    # Attempt to get always active selector
                    try:
                        await cat_item_el.wait_for_selector(always_active_sel, timeout=5000)
                        prev_status = 'always_active'
                    except TimeoutError:
                        print(
                            "WARNING: Cannot get toggle button, assume this is 'always on'")
                cur_status = prev_status

            # maybe uncessary because of cookie_consent
            # scan_result['category'].append(
            #     {'id': optanon_group_id, 'name': category_name, 'prev_status': prev_status, 'cur_status': cur_status})

            cookie_list_ui_avail = (tab_desc_el is not None)
            cookie_list = await extract_cookie_list(self._pref_menu_el, tab_desc_el, optanon_group_id) if self._extract_cookie_list else cookie_list_ui_avail

            if verbose >= 2: print(f"Set group {optanon_group_id=} to status {cur_status}")
            cookie_consent[optanon_group_id] = CategoryConsent(
                category=category_name,
                category_id=optanon_group_id,
                prev_status=convert_status_to_bool(prev_status),
                cur_status=convert_status_to_bool(cur_status),
                # cookie_list=cookie_list # to analyze UI, maybe unnecessary
                # 'name': extract_cookie_category_name(), # may be unncessary
            )
        return cookie_consent

def test_pref_str():
    cookie_dict = {'name': OptanonConsentCookie.consent_cookie_name, 'value': "isIABGlobal=false&datestamp=Sun+Aug+15+2021+11%3A45%3A55+GMT-0400+(Eastern+Daylight+Time)&version=6.20.0&hosts=&consentId=c18e8318-6b34-4e36-8c46-0599c1a79542&interactionCount=1&landingPath=NotLandingPage&groups=1%3A1%2C2%3A1%2C3%3A1%2C4%3A1%2C5%3A1&AwaitingReconsent=false"}
    cookie = OptanonConsentCookie(cookie_dict)
    assert cookie.get_val('groups') == '1%3A1%2C2%3A1%2C3%3A1%2C4%3A1%2C5%3A1'
    assert cookie.get_characteristic_val() ==  '6.20.0'

    cookie_dict = {'name': OptanonConsentCookie.consent_cookie_name, 'value': "isGpcEnabled=0&datestamp=Sat+Oct+05+2024+20%3A21%3A54+GMT-0400+(Eastern+Daylight+Time)&version=202403.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=c724274b-cfb9-45bc-80ba-bc70e7b69e35&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=1%3A1%2C2%3A0%2C3%3A0%2C4%3A0%2C5%3A0&intType=6"}
    cookie = OptanonConsentCookie(cookie_dict)
    print("Category preferences:", cookie.get_cat_prefs())

if __name__ == '__main__':
    test_pref_str()
    print('Tests passed.')
