"""Utils to dump cookies."""

from pathlib import Path
from typing import Dict

from ooutil.cookie_util import get_domain_match_cookies
from ooutil.json_util import dump_to_json_file


def dump_cookies_to_file(url, cookies: Dict, out_file: Path, verbose=1):
    dump_to_json_file({'url': url, 'cookies': cookies}, out_file)
    if verbose > 0:
        print(f'Dumped {len(cookies)} cookies to {out_file}')
    return cookies


def dump_cookies_in_domains(cookies, cookie_domains, out_file: Path):
    acookies = get_domain_match_cookies(cookies, cookie_domains)
    dump_cookies_to_file(list(acookies), out_file)


async def dump_cookies(browser_context, out_file: Path):
    cookies = await browser_context.cookies()
    dump_cookies_to_file(cookies, out_file)


def dump_cookies_sync(browser_context, out_file: Path):
    cookies = browser_context.cookies()
    dump_cookies_to_file(cookies, out_file)
