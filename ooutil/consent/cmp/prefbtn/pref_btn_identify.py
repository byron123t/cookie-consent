"""Analyze the preference buttons and other buttons."""

from typing import List

from asyncio.tasks import ALL_COMPLETED
from colorama import Fore
from pathlib import Path
from pandas.core.frame import DataFrame
from playwright.async_api import async_playwright, Page, TimeoutError, ElementHandle, Error
import asyncio
import pandas as pd

from consent.data.cookie_setting import CookieSetting
from consent.util.default_path import create_data_dir
from ooutil.browser_control import run_in_clean_browser
from ooutil.file import file_empty
from ooutil.type_util import hashabledict


async def _get_pref_btn(frame, pref_btn_sel, verbose=0):
    if verbose >= 2:
        print(f"Get pref btn {pref_btn_sel} on frame {frame.url}")

    if pref_btn_sel.startswith('/html'):
        pref_btn_sel = 'xpath=' + pref_btn_sel
    try:
        # Use 'attached for in the dataset we know the buttons are clickable, even we have to hover some menu.
        # pref_btn = await frame.wait_for_selector(pref_btn_sel, state='attached', timeout=3000)
        # 100ms: too short for bazaarvoice, can we increase to 3000 + launch async? note: 1000ms takes a long time on bostonherald waiting for the banner to disappear, does not timeout in 1000ms
        return await _query_selector_all_with_timeout(frame, pref_btn_sel, verbose=0) # in case there are multiple buttons of the same id, e.g., cloudinary.
        # pref_btn = await frame.wait_for_selector(pref_btn_sel, timeout=3000)
        # return pref_btn
    except TimeoutError as e:
        print('.', end='')
    except Exception as e:
        print('Error wait for selector, reason:', e)
    return []

async def get_pref_btns(page, pref_btn_sels):
    print("Getting pref btn:", pref_btn_sels)
    # await page.pause()

    tasks = [asyncio.create_task(_get_pref_btn(frame, pref_btn_sel)) for frame in page.frames for pref_btn_sel in pref_btn_sels]
    done, pending = await asyncio.wait(tasks, return_when=ALL_COMPLETED)

    pref_btns = []
    for task in done:
        try:
            # btn = task.result()
            # if btn is not None:
                # pref_btns.append(btn)
            pref_btns.extend(task.result())
        except TimeoutError:
            print('.', end='')
            continue
    return pref_btns

async def _get_leaf_elem(elem: ElementHandle, verbose=0):
    try:
        # children = await asyncio.wait_for(elem.query_selector_all('*'), timeout=5)
        children = await asyncio.wait_for(elem.wait_for_selector('*', timeout=3000, state='attached'), timeout=5)
        if children is not None:
            return None # not a leaf.
    except TimeoutError as e:
        if verbose >= 3: print('-', end='')
    except asyncio.TimeoutError:
        if verbose >= 2: print('_get_elem_leaf timeout!')
    return elem # cannot find any child, so should be a leaf.


async def get_leaf_elems(elems, verbose=0):
    if len(elems) == 0:
        return []

    tasks = [asyncio.create_task(_get_leaf_elem(elem)) for elem in elems]
    # done, _ = await asyncio.wait(tasks, return_when=ALL_COMPLETED)
    results = await asyncio.gather(*tasks)
    elems = []
    # for task in done:
    for result in results:
        # result = task.result()
        if result is not None:
            if verbose >= 2: print('Found a leaf elem')
            elems.append(result)
        else:
            if verbose >= 2: print('Found a non-leaf elem')
    return elems

async def _query_selector_all_with_timeout(handle, tag, verbose=0):
    """handle: ElementHandle or Page or Frame that supports wait_for_selector."""
    if verbose >= 2: print(f'_query_selector_all_with_timeout for tag {tag}')
    try:
        # TODO: cancel a task may cause invalid state for asyncio (github.com)
        return await asyncio.wait_for(handle.query_selector_all(tag), timeout=10)
        # return await handle.query_selector_all(tag)
    except TimeoutError as e:
        print('-', end='')
    except Error as e:
        if verbose >= 2: print(f'_query_selector_all_with_timeout error for tag {tag}:', str(e))
    except asyncio.TimeoutError:
        if verbose >= 2: print(f'_query_selector_all_with_timeout timeout for tag {tag}')
    except Exception as e:
        print(f'_query_selector_all_with_timeout exception {str(e)}')
    return []

async def _get_buttons_of_tags(frame, tags, leaf_only=False, verbose=0):
    if verbose >= 2: print('_get_buttons_of_tags', tags, 'on frame', frame.url)
    elems = []
    try:
        tasks = [asyncio.create_task(_query_selector_all_with_timeout(frame, f'{tag}:visible')) for tag in tags]
        # done, pending = await asyncio.wait(tasks, return_when=ALL_COMPLETED)

        # for task in done:
            # elems.extend(task.result())
        results = await asyncio.gather(*tasks)
        for result in results:
            elems.extend(result)

        if leaf_only:
            elems = await get_leaf_elems(elems)
    except asyncio.TimeoutError:
        print('Query buttons timeout!')

    return elems

async def _get_buttons(frame, verbose=0):
    if verbose >= 2: print('_get_buttons on frame', frame.url)
    try:
        leaf_only_buttons = await _get_buttons_of_tags(frame, ['div'], leaf_only=True)
        buttons = await _get_buttons_of_tags(frame, ['a', 'button', 'span'])
        return leaf_only_buttons + buttons
    except Exception as e:
        print('_get_buttons: Exception', str(e))
    return []


async def get_buttons(page: Page, verbose=2):
    if verbose >= 2: print("Get buttons")
    tasks = [asyncio.create_task(_get_buttons(frame)) for frame in page.frames]
    # done, pending = await asyncio.wait(tasks, return_when=ALL_COMPLETED)
    found_buttons_in_frames = await asyncio.gather(*tasks)

    buttons = []
    # for task in done:
    for found_buttons in found_buttons_in_frames:
        buttons.extend(found_buttons)
        # try:
            # buttons.extend(task.result())
        # except TimeoutError:
            # print('.', end='')
            # continue
    return buttons


async def _navigate_to_url(page: Page, url: str, reload=False, verbose=1):
    if verbose >= 2: print(f'_navigate_to_url Go to {url}')
    try:
        if not reload:
            await page.goto(url, wait_until='networkidle', timeout=10000)
        else:
            await page.reload(wait_until='networkidle', timeout=10000)
    except TimeoutError as e:
        print('Navigation time out, continue ...')

    await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
    if verbose >= 1: print("Scrolled to bottom.")
    await asyncio.sleep(3)

async def _get_pref_btns_on_page(page: Page, pref_btn_sels):
    pref_btns = await get_pref_btns(page, pref_btn_sels)
    buttons = await get_buttons(page)

    return pref_btns, buttons


async def get_pref_btns_and_other_btns(page: Page, url: str, pref_btn_sels, try_reload=False):
    await _navigate_to_url(page, url)
    pref_btns, buttons = await _get_pref_btns_on_page(page, pref_btn_sels)
    n_pref_btns, n_pref_btn_sels = len(pref_btns), len(pref_btn_sels)
    # May disable this when extracting from files (create a pref btn dataset).
    if try_reload and n_pref_btns == 0: # TODO: why not reload on riotgames.com automatically?
        print('Try to reload ...')
        await _navigate_to_url(page, url, reload=True)
        pref_btns, buttons = await _get_pref_btns_on_page(page, pref_btn_sels)
    if n_pref_btns != n_pref_btn_sels:
        print(f'Warning: {n_pref_btns=} not equal {n_pref_btn_sels=}')
    return pref_btns, buttons


async def get_attr_dict(elem: ElementHandle, include_el):
    try:
        text_content = await elem.text_content()
        result = {
            'id': await elem.get_attribute('id'),
            'class': await elem.get_attribute('class'),
            'tag_name': await elem.evaluate('e => e.tagName'),
            'text_content': text_content.strip() if text_content else '',
            'inner_text': (await elem.inner_text()).strip(),
            'aria_label': await elem.get_attribute('aria-label'),
            'title': await elem.get_attribute('title'),
            'href': await elem.get_attribute('href'),
            'onclick': await elem.get_attribute('onclick'),
        }
        if include_el:
            result['el'] = elem
        return result
    except Error as e:
        print('Error getting attributes:', e)
    return None


async def get_btn_attrs(buttons: List[ElementHandle], include_el=False):
    if len(buttons) == 0:
        return set()

    tasks = [asyncio.create_task(get_attr_dict(button, include_el=include_el)) for button in buttons]
    # done, pending = await asyncio.wait(tasks, return_when=ALL_COMPLETED)
    # button_attrs = [task.result() for task in done]
    button_attrs = await asyncio.gather(*tasks)
    button_attrs = [hashabledict(attr) for attr in button_attrs if attr is not None] # some get_attribute may error.

    return set(button_attrs)


def check_btn_inclusion(pref_btn_attrs, button_attrs):
    # assert len(button_attrs.intersection(pref_btn_attrs)) > 0:
    for pref_btn_attr in pref_btn_attrs:
        if pref_btn_attr in button_attrs:
            for button_attr in button_attrs:
                if button_attr['id'] == pref_btn_attr['id']:
                    print('Button attrs with same id:')
                    print(button_attr)
            raise ValueError(f'Pref btn is not among all the found buttons. {pref_btn_attr=}')

async def get_and_save_btn_attrs(site: str, pref_btns: List[ElementHandle], buttons: List[ElementHandle], out_file: Path=None):
    print('Extract and save data')

    # Extract buttons on frames, so still need to record the button on the frames if there is no
    pref_btn_attrs = await get_btn_attrs(pref_btns)
    if len(pref_btn_attrs) == 0:
        print('Warning: Cannot get any attributes for pref btns.')
        # return
    print('Pref btn attrs:', pref_btn_attrs)

    button_attrs = await get_btn_attrs(buttons)

    # check_btn_inclusion(pref_btn_attrs, button_attrs)

    all_attrs = list(pref_btn_attrs.union(button_attrs))
    for attr in all_attrs:
        attr['pref_btn'] = attr in pref_btn_attrs
        attr['site'] = site

    df = pd.DataFrame.from_records(all_attrs)
    if out_file is not None:
        df.to_csv(out_file)
        print(f'Written data to {out_file}')


async def get_and_save_pref_btn_df_on_page(brcontext, page, url, pref_btn_sels, site, out_file=None):
    pref_btns, buttons = await get_pref_btns_and_other_btns(page, url, pref_btn_sels)

    # if out_file is not None:
    #     screenshot_file = out_file.with_suffix('.png')
    #     await page.screenshot(path=screenshot_file)

    # Extract buttons on frames, so still need to record the button on the frames if there is no
    # if len(pref_btns) == 0: #     print('Not found pref btn, no saving data ...') #     return False

    if len(pref_btns) > 0:
        print(f'{Fore.GREEN} Found {len(pref_btns)} pref btn.', Fore.RESET)
    else:
        print(f'{Fore.WHITE}Found {len(pref_btns)} pref btn.', Fore.RESET)
    await get_and_save_btn_attrs(site, pref_btns, buttons, out_file)
    return len(pref_btns)


async def get_and_save_pref_btn_df(site: str, out_dir: Path, force: bool, use_wpr: bool):
    out_file = out_dir / f'{site}.csv'
    try:
        pref_btn_sels = CookieSetting.get_field(site, 'pref_buttons')
        if len(pref_btn_sels) == 0: # do nothing as this site has no pref buttons.
            return True

        # if not force and file_exists_not_empty_and_old(out_file): return True

        out_file.touch()

        url = CookieSetting.get_opt_page(site)

        return await run_in_clean_browser(
            use_wpr=use_wpr, headless=True, url=url, func=get_and_save_pref_btn_df_on_page, site=site, pref_btn_sels=pref_btn_sels, out_file=out_file)
    except Exception as e:
        print(f"An error occurs at site {site}:", e)
    finally:
        raise ValueError("Need to prevent processes delete others' empty files.")
        if out_file.exists() and file_empty(out_file):
            out_file.unlink(missing_ok=True)

    return False

async def main():
    out_dir = create_data_dir('2021-03-01') / 'pref_btn_v7'
    out_dir.mkdir(exist_ok=True)

    force = False
    # TODO: collect data on websites that do not have any preference buttons.
    sites = CookieSetting.get_all_sites()
    for site in ['unilad.co.uk', 'searchenginejournal.com']: sites.remove(site) # except hidden pref btn.
    for site in list(sites):
        if not await get_and_save_pref_btn_df(site, out_dir, force=force, use_wpr=True):
            print('Retry with live website ...')
            # Bug: will not run because csv will be empty so skipping this website.
            await get_and_save_pref_btn_df(site, out_dir, force=True, use_wpr=False)


if __name__ == '__main__':
    asyncio.run(main())
