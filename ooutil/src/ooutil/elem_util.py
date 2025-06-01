"""Utilities for elements."""

import asyncio

from bs4 import BeautifulSoup
from playwright.async_api import ElementHandle, Frame


async def click_js(elem: ElementHandle):
    await elem.evaluate_handle('e => e.click()')  # workaround hidden by a welcome pop-up


async def is_visible(ahandle: ElementHandle):
    js_function = """
        function isVisible(elem) {
            function parseValue(value) {
                var parsedValue = parseInt(value);
                if (isNaN(parsedValue)) {
                    return 0;
                } else {
                    return parsedValue;
                }
            }

            if (!elem) elem = this;
            if (!(elem instanceof Element)) return false;
            let visible = true;
            const style = getComputedStyle(elem);

            // for these rules the childs cannot be visible, directly return
            if (style.display === 'none') return false;
            if (style.opacity < 0.1) return false;
            if (style.visibility !== 'visible') return false;

            // for these rules a child element might still be visible,
            // we need to also look at the childs, no direct return
            if (elem.offsetWidth + elem.offsetHeight + elem.getBoundingClientRect().height +
                elem.getBoundingClientRect().width === 0) {
                visible = false;
            }
            if (elem.offsetWidth < 10 || elem.offsetHeight < 10) {
                visible = false;
            }
            const elemCenter = {
                x: elem.getBoundingClientRect().left + elem.offsetWidth / 2,
                y: elem.getBoundingClientRect().top + elem.offsetHeight / 2
            };
            if (elemCenter.x < 0) visible = false;
            if (elemCenter.x > (document.documentElement.clientWidth || window.innerWidth)) visible = false;
            if (elemCenter.y < 0) visible = false;
            if (elemCenter.y > (document.documentElement.clientHeight || window.innerHeight)) visible = false;

            // check the child nodes
            if (!visible) {
                let childrenCount = elem.childNodes.length;
                for (var i = 0; i < childrenCount; i++) {
                    let isChildVisible = isVisible(elem.childNodes[i]);
                    if (isChildVisible) {
                        return isChildVisible;
                    }
                }
            }

            return visible;
        }"""
    return await ahandle.evaluate(js_function)


async def get_elements(soup_or_frame, css_selector):
    if isinstance(soup_or_frame, BeautifulSoup):
        return soup_or_frame.select(css_selector)
    elif isinstance(soup_or_frame, Frame):
        try:
            return await asyncio.wait_for(soup_or_frame.query_selector_all(css_selector), timeout=5)
        except asyncio.TimeoutError:
            print('WARNING: get_elements query_selector_all timeout')
            return []

    raise ValueError(
        f"Unsupported type {type(soup_or_frame)=} {soup_or_frame=}")