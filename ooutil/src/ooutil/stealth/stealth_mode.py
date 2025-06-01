"""Stealth mode for browser."""
from pathlib import Path

STEALTH_MODE_TEST_URL = 'https://bot.sannysoft.com/'


def get_steath_js_content():
    js_file = Path(__file__).parent / 'stealth.min.js'
    assert js_file.exists(), f"{js_file} not found"

    return js_file.read_text()


async def make_stealth(page):
    await page.add_init_script(get_steath_js_content())
