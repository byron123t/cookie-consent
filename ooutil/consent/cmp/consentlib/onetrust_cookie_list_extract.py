from typing import Dict, List, Optional

from playwright.async_api import ElementHandle, TimeoutError

from ooutil.browser_control import try_click, try_get_attribute


async def extract_cookie_list(pref_menu_el: Optional[ElementHandle], tab_desc_el: Optional[ElementHandle], optanon_group_id: str, verbose=0):
    cookie_list: List[Dict] = []
    if pref_menu_el is not None and tab_desc_el is not None:
        try:
            if verbose >= 2:
                print("Extract cookie list ...")

            host_list_btn = await tab_desc_el.wait_for_selector('.category-host-list-btn, .category-host-list-handler', state='attached', timeout=3000)
            if host_list_btn is None:
                raise ValueError('Cannot get host_list_btn')

            data_parent_id = await try_get_attribute(host_list_btn, 'data-parent-id', 'Cannot get data-parent-id')
            assert data_parent_id == optanon_group_id, f"{data_parent_id=} != {optanon_group_id=}"

            await try_click(host_list_btn)

            cookie_list = await _extract_cookie_list(pref_menu_el)
            if verbose >= 4:
                print("Cookie list:", cookie_list)

            back_btn = await pref_menu_el.wait_for_selector('#back-arrow, #ot-back-arrow, #ot-back-arw', state='attached', timeout=5000)

            if back_btn is None:
                raise ValueError("Cannot get back btn")

            # svg's parent is the back button
            await back_btn.evaluate_handle('e => e.parentElement.click()')
            # await back_btn.click(force=True) # This is a svg, so must use click
            # await try_click(page, [back_btn]) # does not work if the above does not.
        except Exception as e:
            if verbose >= 1:
                print("Cannot extract cookie list", e)
    return cookie_list


async def _extract_cookie_list(pref_menu_el):  # current_cookie_category
    async def extract_vendor_value(vendor_host, field_name, field_sel):
        try:
            field = await vendor_host.wait_for_selector(field_sel, state='attached', timeout=3000)
        except TimeoutError as e:
            # TODO: this is slow due to waiting for 3 sec, should skip all together if 1 elem does not have this.
            print(e)
            return ''

        field_val = await field.text_content()
        # print(f'{field_val}')
        if field_name in ['name', 'host']:
            field_val = field_val.split()[0]
        field_val = field_val.strip()
        groups = re.match(field_name.title() + r"(.*)", field_val)
        return groups.group(1)
    vendor_hosts = []
    vendor_list_el = await pref_menu_el.wait_for_selector('#vendors-list, #ot-host-lst')
    vendor_host_els = await vendor_list_el.query_selector_all('.vendor-host, .ot-host-info')
    print("number of host items:", len(vendor_host_els))
    for vendor_host_el in vendor_host_els:
        vendor_host = {}
        for field_name in ['name', 'host', 'duration']:
            vendor_host[field_name] = await extract_vendor_value(vendor_host_el, field_name, f'.cookie-{field_name}-container, .ot-c-{field_name}')
        vendor_hosts.append(vendor_host)
    return vendor_hosts
