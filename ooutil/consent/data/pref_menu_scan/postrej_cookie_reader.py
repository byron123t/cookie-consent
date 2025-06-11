# %%
"""Read post-rejection cookies."""

from pathlib import Path
from multiprocessing import Pool
import json
from typing import Dict, List
import random

import pandas as pd
from consent.cmp.consentlib.consent_cookie import ConsentCookie

from consent.cmp.consentlib.factory import ConsentLibFactory
from consent.cmp.consentlib.consent_lib import find_cookie_in_page_cookies
from src.ooutil.cookie_util import url_domain_match, get_brower_cookies, parse_cookie_str
from src.ooutil.type_util import hashabledict

import sys; import importlib; importlib.reload(sys.modules['ooutil.cookie_util'])
from src.ooutil.cookie_util import url_domain_match, get_brower_cookies, parse_cookie_str

SENT_PREFIX = 'sent_'


def _parse_cookies(cookie_dicts):
    cookies = []
    for cookie_dict in cookie_dicts:
        for parsed_cookie in parse_cookie_str(cookie_dict['cookie']):
            parsed_cookie['request_url'] = cookie_dict['request_url']
            cookies.append(parsed_cookie)
    return cookies


def _contain_cookie(cookies: pd.DataFrame, consent_cookie: ConsentCookie, verbose=0):
    if len(cookies) == 0:
        return False
    characteristic_val = consent_cookie.get_characteristic_val()
    found = cookies[(cookies.name == consent_cookie.cookie['name']) & (cookies.domain == consent_cookie.cookie['domain']) & (cookies.value.str.contains(characteristic_val))]
    if verbose >= 3:
        print(f'{consent_cookie.cookie=}')
        print(f'{characteristic_val=}')
    return len(found) > 0


def is_cookie_file_valid(sent_brcookies, page_url: str, consent_cookie: ConsentCookie, postrej_cookies_file, verbose=3):
    if not url_domain_match(page_url, consent_cookie.cookie['domain']):
        if verbose >= 2: print(f"Unmatch url and consent cookie domain:", page_url, consent_cookie.cookie['domain'], f'{postrej_cookies_file.parent.name}/{postrej_cookies_file.name}')
        return False

    if not _contain_cookie(sent_brcookies, consent_cookie):
        if verbose >= 2: print(f"Post rej cookie not contain consent cookie, {postrej_cookies_file.parent.name}/{postrej_cookies_file.name} {consent_cookie.cookie['name']=} {consent_cookie.cookie['domain']=}")
        return False

    return consent_cookie is not None


def read_postrej_sent_cookies_from_file(postrej_cookies_file: Path, consent_cookie: ConsentCookie, verbose=2, debug=False):
    """Map sent cookies to browser cookies and return them."""
    if verbose >= 3: print(f"Process {postrej_cookies_file.name}")
    try:
        postrej_info = json.loads(postrej_cookies_file.read_text())
    except Exception as e:
        print(f"Error loading cookie for site {postrej_cookies_file.parent.name}/{postrej_cookies_file.name}: {e}")
        return []

    br_cookies = pd.DataFrame(postrej_info['browser_cookies'])

    sent_cookies = _parse_cookies(postrej_info['sent_cookies'])
    sent_cookies = set([hashabledict(cookie) for cookie in sent_cookies])

    sent_brcookies = []
    for sent_cookie in sent_cookies:
        # for _, row in get_brower_cookies(br_cookies, sent_cookie)[['name', 'domain', 'path']].iterrows():
        if debug and sent_cookie['name'] == 'OptanonConsent':
            print('check')
        # match_value = (sent_cookie['name'] != consent_cookie.cookie['name']) # ignore matching value of OptanonConsent cookie as it is reordered.
        if sent_cookie['name'] == consent_cookie.cookie['name']:
            partial_value = consent_cookie.get_characteristic_val()
        else:
            partial_value = None
        for brcookie in get_brower_cookies(br_cookies, sent_cookie, partial_value).to_dict('records'):
            brcookie['request_url'] = sent_cookie['request_url']
            for sent_key, sent_val in sent_cookie.items():
                brcookie[SENT_PREFIX + sent_key] = sent_val
            if debug and brcookie['name'] == 'OptanonConsent': print('=============Found!!!!!')
            sent_brcookies.append(brcookie)

    site = postrej_cookies_file.parent.name
    for cookie in sent_brcookies:
        cookie['site'] = site
        if 'load_start_time' in postrej_info:
            cookie['load_start_time'] = postrej_info['load_start_time']
            cookie['load_end_time'] = postrej_info['load_end_time']
            cookie['page_url'] = postrej_info['url']

    # Verify validity
    if not is_cookie_file_valid(pd.DataFrame(sent_brcookies), postrej_info['url'], consent_cookie, postrej_cookies_file):
        if verbose >= 3: print(f"WARNING: {postrej_cookies_file} invalid")
        return None

    return sent_brcookies


def read_sent_cookies_by_read_args(cookie_read_args, keep_sent_cookie, verbose=2):
    if verbose >= 2: print("Num postrej cookie files:", len(cookie_read_args))
    random.shuffle(cookie_read_args) # May spread loads more evenly
    pool = Pool(min(40, len(cookie_read_args))) # number of cores you want to use
    # pool = Pool(min(1, len(cookie_read_args))) # number of cores you want to use

    sent_cookies_list = pool.starmap(read_postrej_sent_cookies_from_file, cookie_read_args) #creates a list of the loaded df's

    failed_sites = set()
    sent_cookies = []
    for a_sent_cookies, cookie_read_arg in zip(sent_cookies_list, cookie_read_args):
        if a_sent_cookies is None or len(a_sent_cookies) == 0:
            failed_sites.add(cookie_read_arg[0].parent.name)
            continue

        sent_cookies.extend(a_sent_cookies)

    if verbose >= 2: print(f"{len(failed_sites)} sites with corrupted cookie files:", sorted(list(failed_sites)))

    df = pd.DataFrame(sent_cookies)
    if not keep_sent_cookie:
        cols = [col for col in df.columns if not col.startswith(SENT_PREFIX)]
        return df[cols]
    return df


def get_read_args_in_site_dir(site_dir: Path, verbose=0):
    log_file = site_dir / 'log.json'
    try:
        log = json.loads(log_file.read_text())
    except Exception as e:
        if verbose >= 2: print(f"Cannot read {log_file}: {e}")
        return None

    if log['error'] is not None:
        return None

    brcookies_file = (site_dir / 'postrej_browser_cookies.json')
    try:
        brcookies_info = json.loads(brcookies_file.read_text())
    except Exception as e:
        if verbose >= 2: print(f"Cannot read {brcookies_file}: {e}")
        return

    consent_lib_name = log['scan_result']['consent_lib_name']
    if verbose >= 2: print(f'{consent_lib_name=}')

    consent_cookie_cls = ConsentLibFactory.get_consent_cookie_class_by_name(consent_lib_name)
    consent_cookie_dict = find_cookie_in_page_cookies(
        brcookies_info['browser_cookies'], brcookies_info['url'], consent_cookie_cls.consent_cookie_name, warnings=None)
    if consent_cookie_dict is None:
        if verbose >= 2: print(f"Cannot get consent cookit for {site_dir}")
        return None

    consent_cookie = consent_cookie_cls(consent_cookie_dict)

    for postrej_cookies_file in site_dir.glob('postrej_*_cookies.json'):
        if postrej_cookies_file.name == 'postrej_browser_cookies.json':
            continue
        yield (postrej_cookies_file, consent_cookie)

def get_read_args_in_scans(scan_dirs: List[Path]):
    read_args = []
    for scan_dir in scan_dirs:
        for site_dir in scan_dir.glob('*'):
            if not site_dir.is_dir():
                continue
            site_read_args = list(get_read_args_in_site_dir(site_dir))
            if site_read_args is not None:
                read_args.extend(site_read_args)
    return read_args


def read_postrej_sent_cookies_in_scans(scan_dirs: List[Path], keep_sent_cookie=False):
    # raise NotImplementedError('need to filter out consent cookies.')
    read_args = get_read_args_in_scans(scan_dirs)
    return read_sent_cookies_by_read_args(read_args, keep_sent_cookie)


from ooutil.url_util import is_same_suffixed_domain

def test_get_valid_cookie_files(site_dir: Path, verbose=1):
    log_file = site_dir / 'log.json'
    try:
        log = json.loads(log_file.read_text())
    except Exception as e:
        if verbose >= 2: print(f"Cannot read {log_file}: {e}")
        return

    if log['error'] is not None:
        return []

    try:
        brcookies_file = (site_dir / 'postrej_browser_cookies.json')
        page_url = json.loads(brcookies_file.read_text())['url']
    except Exception as e:
        if verbose >= 2: print(f"Cannot read {brcookies_file}: {e}")
        return

    consent_lib_name = log['scan_result']['consent_lib_name']
    if verbose >= 2: print(f'{consent_lib_name=}')
    # cat_prefs = read_cat_prefs_in_dir(site_dir)
    # if verbose >= 2: print(cat_prefs)
    for postrej_cookies_file in site_dir.glob('postrej_*_cookies.json'):
        if postrej_cookies_file.name == 'postrej_browser_cookies.json':
            continue

        # TODO: compare with consent cookie's domain.
        subpage_url = json.loads(postrej_cookies_file.read_text())['url']
        if not is_same_suffixed_domain(subpage_url, page_url):
            if verbose >= 1: print(f'{postrej_cookies_file.parent.name}/{postrej_cookies_file.name} not valid')
            return

        # TODO: to check sent cookies. This may be very heavy and maybe just match the consent cookie domain
        # sent_brcookies = read_postrej_sent_cookies_from_file(postrej_cookies_file)
        # if not is_cookie_file_valid(sent_brcookies, page_url, consent_lib_name):
        #     if verbose >= 1: print(f'{postrej_cookies_file} not valid')
        #     return


if __name__ == '__main__':
    pass
    # %%
    from consent.util.default_path import get_data_dir, get_data_dir2
    scan_dirs = [get_data_dir2('2023-04-14/pref_menu_scan_test/')]
    print(scan_dirs)
    # scan_dirs = [get_data_dir('2021-08-12/pref_menu_scan_10k_20k/')]
    # scan_dirs = [get_data_dir('2021-08-12/pref_menu_scan/')]
    # scan_dirs = [get_data_dir('2021-08-12/test_pref_menu_scan/')]
    read_postrej_sent_cookies_in_scans(scan_dirs)

    # %%
    site_dirs = list(get_data_dir('2021-08-12/pref_menu_scan_10k_20k/').glob('*'))
    assert all(d.is_dir() for d in site_dirs)
    # %%
    site_dir = get_data_dir('2021-08-12/pref_menu_scan_0k_10k/acrobat.com')
    test_get_valid_cookie_files(site_dir)

    # %%
    # Expect to find some invalid post-rejection cookie file.
    # Should store/cache the list of invalid files.
    pool = Pool(40) # number of cores you want to use
    results = pool.map(test_get_valid_cookie_files, site_dirs)

    # %%
    # parallel_read_postrej_sent_cookies_in_site_dirs()

# def read_postrej_sent_cookies_for_site(site_dir):
#     # sent_cookies = []
#     # for postrej_cookies_file in site_dir.glob('postrej_*.json'): # / 'postrej_cookies.json'
#     #     sent_cookies.extend(read_postrej_sent_cookies_from_file(postrej_cookies_file))
#     cookies_files = list(site_dir.glob('postrej_*_cookies.json'))
#     cookies_files = filter_cookies_files(cookies_files)
#     if len(cookies_files) == 0:
#         return []
#     pool = Pool(min(4, len(cookies_files))) # number of cores you want to use
#     sent_cookies_list = pool.starmap(read_postrej_sent_cookies_from_file, cookies_files) #creates a list of the loaded df's
#     sent_cookies = [cookie for sent_cookies in sent_cookies_list for cookie in sent_cookies]

#     # for cookie in sent_cookies: # set in read_postrej_file
#     #     cookie['site'] = site_dir.name
#     return sent_cookies

# def read_postrej_sent_cookies(site_dirs):
#     sent_cookies = []
#     for site_dir in tqdm(site_dirs):
#         sent_cookies.extend(read_postrej_sent_cookies_for_site(site_dir))

#     return pd.DataFrame(sent_cookies).drop_duplicates()

# def obsolete_parallel_read_postrej_sent_cookies(data_dir, keep_sent_cookie=False):
#     """Assume structured data_dir /site / data_files. Could not aggregate sent cookies to reduce computation because we need to map to the same state of browser cookies."""
#     cookies_files = list(data_dir.glob('*/postrej_*.json'))[:]
#     cookies_files = filter_cookies_files(cookies_files)
#     return parallel_read_sent_cookies(cookies_files, keep_sent_cookie)

# def obsolete_parallel_read_postrej_sent_cookies_in_site_dirs(site_dirs: List[Path], keep_sent_cookie=False):
#     """Assume structured data_dir /site / data_files. Could not aggregate sent cookies to reduce computation because we need to map to the same state of browser cookies."""
#     cookies_files = [afile for site_dir in site_dirs for afile in site_dir.glob('*/postrej_*.json')]
#     cookies_files = filter_cookies_files(cookies_files)
#     return parallel_read_sent_cookies(cookies_files, keep_sent_cookie)

# def filter_cookies_files(cookies_files: List[Path]):
#     # Filter out cookie files which do not contain sent cookies.
#     return [f for f in cookies_files if f.name != 'postrej_browser_cookies.json']