#%%
"""Scan through websites and extract their preference buttons.
page -> attrs of buttons -> feats of buttons -> probas of buttons -> argmax.
Combine featurizer and classifer to extract the preference buttons.
"""

import asyncio
from typing import List, Optional
from ooutil.async_util import asyncio_wait_for_timeout
from playwright.async_api import Page
import numpy as np
import pandas as pd

from consent.cmp.prefbtn.pref_btn_clf import PrefBtnClf
from consent.cmp.prefbtn.pref_btn_identify import get_buttons, get_btn_attrs
from consent.cmp.prefbtn.pref_btn_featurizer import featurize_attr_df
from ooutil.browser_control import get_selector


async def get_pref_btns(page: Page, top_n: int, verbose=0):
    buttons = await get_buttons(page)
    if len(buttons) == 0:
        print('WARNING: no buttons found.')
        return []

    btn_attrs = pd.DataFrame(await get_btn_attrs(buttons, include_el=True))

    if len(btn_attrs) == 0:
        print('WARNING: empty btn attrs.')
        return []

    if verbose >= 2:
        print(f'{btn_attrs=}')

    # assert len(btn_attrs) == len(buttons) # get attr may failed?
    button_feat_df, _ = featurize_attr_df(btn_attrs)

    if verbose >= 2:
        print(f'{button_feat_df=}')

    top_n_btn_attrs = PrefBtnClf.get_top_n(btn_attrs, button_feat_df, top_n)
    assert len(top_n_btn_attrs) <= top_n, f'{len(top_n_btn_attrs)=} larger than {top_n=}'
    return top_n_btn_attrs['el'].tolist()

async def extract_pref_btns(page):
    return await get_pref_btns(page, top_n=5)

async def get_pref_btns_by_rules(page: Page, warnings: Optional[List], verbose=2):
    selector = '.ot-sdk-show-settings, .optanon-toggle-display, #onetrust-pc-btn-handler, #ot-sdk-btn, a[onclick*="OneTrust.ToggleInfoDisplay()"], a[onclick*="Optanon.ToggleInfoDisplay()"], #teconsent, a[href*="Cookiebot.renew()"], button.t-preference-button'
    try:
        found = await asyncio_wait_for_timeout(page.query_selector_all(selector), timeout=5, default_val=[])
        if verbose >= 2:
            print(f"Found {len(found)} btns by rules.")
        return found
    except TimeoutError:
        if warnings: warnings.append("Timeout when getting pref btn by rules")
    return []

async def extract_pref_btn_selectors(page: Page, warnings: Optional[List], use_rules=True):
    """Return (frame_url, selector in the frame)
    Because sometimes the get_selector does not work such as on jrdunn.com, in this case, return the pref btn instead
    """
    results = []
    pref_btns = []
    if use_rules:
        pref_btns += await get_pref_btns_by_rules(page, warnings)
    pref_btns += await extract_pref_btns(page)
    # print(f'{pref_btns}=')
    # TODO: change the following to ooutil.page_util.get_opt_btn_selectors
    for pref_btn in pref_btns:
        try:
            result = await asyncio_wait_for_timeout(get_selector(page, pref_btn))
            if result is not None:
                results.append(result)
        except Exception as e:
            msg = f"Error extract pref btns: {e}"
            if warnings: warnings.append(msg)
            print('WARNING:', msg)

    # When finder.js cannot find a pref btn selector
    if len(results) == 0 and len(pref_btns) > 0:
        results = pref_btns[:1]  # Try only the first pref btn because clicking on it may lead to

    return results


# [obsolete] now use the top-k buttons.
# return await predict_btns(button_feat_df, btn_attrs['el'])
# async def predict_btns(button_feat_df, buttons):
#     """Predict and filter out buttons based on attr."""
#     # TODO: get the max probability? # preds = PrefBtnClf.get_clf().predict_proba(button_feat_df) # found_btn_idx = np.argmax(preds[:,1])
#     preds = PrefBtnClf.get_clf().predict(button_feat_df)
#     found_btns = []
#     for found_btn_idx in np.flatnonzero(preds):
#         found_btn = buttons.iloc[found_btn_idx]
#         if await found_btn.is_visible():
#             found_btns.append(found_btn)
#     return found_btns

# async def test_get_selectors():
#     url = 'https://siemens.com'
#     selectors = await PrefBtnExtractor.get_selectors(url)
#     assert selectors is not None
#     print(f"Selectors of {url=}: {selectors=}")

#     url = 'https://overleaf.com'
#     selectors = await PrefBtnExtractor.get_selectors(url)
#     assert len(selectors) == 0, f"{selectors=}"
#     print(f"Selectors of {url=}: {selectors=}")

# if __name__ == '__main__':
#     import asyncio
#     asyncio.run(test_get_selectors())

# %%
async def _notebook():
    # %%
    import asyncio

    from io import BytesIO
    from IPython.display import display
    from PIL import Image

    from playwright.async_api import async_playwright

    from ooutil.browser_async import goto_ignore_timeout, try_click

    # %%
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch()
    brcontext = None

    # %%
    if brcontext is not None:
        await brcontext.close()
    brcontext = await browser.new_context()
    # %%
    url = "https://opendns.com/"

    page = await brcontext.new_page()
    await goto_ignore_timeout(page, url)
    display(Image.open(BytesIO(await page.screenshot())))

    # %%
    for btn in await get_pref_btns(page):
        if await try_click(btn):
            break
    await asyncio.sleep(2) # fade-in menu

    # %%
    # Expect a cookie preference menu is displayed here.
    display(Image.open(BytesIO(await page.screenshot())))

    # %%
    await brcontext.close()
    brcontext = None

    # %%
    await browser.close()
    await playwright.stop()
    # %%

# from consent.data.pref_btn_site import PrefBtnSites
# from ooutil.browser_control import goto_ignore_timeout_error, run_in_clean_browser
# from ooutil.url_util import get_suffixed_domain
# async def get_pref_btns_with_cached_selectors(page):
#     selectors = await PrefBtnExtractor.get_selectors(page.url)
#     if selectors is None:
#         return None
#     els = []
#     for selector in selectors:
#         try:
#             els.append(await page.wait_for_selector(selector, state='attached', timeout=5000))
#         except Exception as e:
#             raise e
#     return els

# async def activate_pref_menu_sel(page, pref_btn_sel):
#     try:
#         print(f"Wait for pref btn {pref_btn_sel}")
#         pref_btn = await page.wait_for_selector(pref_btn_sel, state='attached', timeout=5000)
#         # pref_btn = await page.wait_for_selector(pref_btn_sel, state='visible', timeout=5000)
#     except TimeoutError:
#         print("Cannot get the preference button.")
#         return {}

#     await asyncio.sleep(1)  # the menu fades in for about 1 sec.

#     if not (await pref_btn.is_visible()):
#         print("The preference button is not visible.")
#         return {}

#     # await pref_btn.click()
#     # workaround hidden by a welcome pop-up
#     await pref_btn.evaluate_handle('e => e.click()')
#     print("Clicked the pref btn.")

# class PrefBtnExtractor:
#     """Cached pref-btn extractor."""

#     @classmethod
#     async def get_selectors(cls, url: str, verbose=2):
#         """Get selector for the pref button on the URL. Return None on failure."""
#         # TODO: re-scan with url
#         selectors = PrefBtnSites.get_selectors_by_domain(get_suffixed_domain(url))
#         if selectors is None:
#             if verbose >= 2: print(f"Pref-btn of {url=} not found in cache, run full pref-btn extractor")
#             selectors = await get_pref_btn_selectors_on_url(url)
#         return selectors


# async def get_pref_btn_selectors_on_page(page: Page):
#     """Get pref btn selectors on loaded page."""
#     return await get_selectors(page, await get_pref_btns(page))


# async def get_pref_btn_selectors(brcontext, page, url):
#     await goto_ignore_timeout_error(page, url)
#     return await get_pref_btn_selectors_on_page(page)


# async def get_pref_btn_selectors_on_url(url: str):
#     try:
#         return await run_in_clean_browser(use_wpr=False, headless=True, url=url, func=get_pref_btn_selectors)
#     except Exception:
#         pass
#     return None

# async def extract_pref_btns(page):
#     try:
#         pref_btns = await get_pref_btns_with_cached_selectors(page)
#         if pref_btns is not None:
#             return pref_btns
#     except Exception as e:
#         print("Cannot get from cache (maybe due to dynamic web pages), error:", e)

#     print("Try to predict pref btns again.")
#     # TODO: reenable these; url contains random numbers, so disabled the following ...
#     # pref_btn_selectors = await get_selectors(page, pref_btns)
#     # PrefBtnExtractor.set_selectors(page.url, pref_btn_selectors)
#     return pref_btns
