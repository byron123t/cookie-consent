"""Automtated control of web browsers."""

from typing import List
import re

from playwright.async_api import ElementHandle

from consent.util.env import get_data_dir

async def get_selectors(page, elements: List[ElementHandle]):
    # await page.evaluate("async () => await import('https://medv.io/finder/finder.js').then(m => finder = m)") # not work on facebook.com
    finder_file = get_data_dir('2021-03-21') / 'finder.js'
    finder_script = finder_file.read_text()
    use_eval = False
    if use_eval:
        # Evaluate directly may have conflict with website.
        finder_script = re.sub('export function finder', 'function finder', finder_script)
        await page.evaluate(finder_script)
        return [await el.evaluate("async (e) => await finder(e, {seedMinLength:4})") for el in elements]
    else:
        # Loading from network: may need to wait for finder to load.
        # await page.add_script_tag(content='import {finder} from "https://medv.io/finder/finder.js"; window.finder = finder', type='module')
        # TODO: retry if _finder not defined.
        await page.add_script_tag(content=finder_script + '\nwindow.__finder = finder;', type='module') # export finder to window
        # await asyncio.sleep(3)  # does not help.
        return [await el.evaluate("async (e) => await __finder(e, {seedMinLength:4})") for el in elements]
        # return [await page.evaluate("async (e) => await finder(e, {seedMinLength:4})", el) for el in elements]
