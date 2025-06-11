"""Read cookies from HAR files."""

from pathlib import Path
from multiprocessing import Pool
import json
from typing import Dict, List

import pandas as pd
from tqdm import tqdm

from consent.cmp.consentlib.consent_cookie import ConsentCookie
from consent.cmp.consentlib.consent_lib import find_cookie_in_page_cookies
from consent.cmp.consentlib.factory import ConsentLibFactory
from consent.util.default_path import get_data_dir
from consent.consistency.util import get_scan_dirs, get_scan_root_dir, get_data_dir2_by_location
from src.ooutil.cookie_util import get_brower_cookies
from src.ooutil.compress.compress_json import load
from src.ooutil.cookie_util import url_domain_match, get_brower_cookies, parse_cookie_str
from src.ooutil.type_util import hashabledict
from src.ooutil.url_util import get_suffixed_domain_with_dot_prefix


def get_sent_cookies(har_dict: Dict, site: str, page_url: str, verbose=0):
    har_df = pd.DataFrame.from_records(har_dict['log']['entries'])
    har_df['site'] = site
    if verbose >= 2:
        print(f"Number of entries: {len(har_df):,d}")
    requests = pd.DataFrame.from_records(har_df.request).explode('cookies')
    requests_with_cookies = requests[~requests.cookies.isna()]
    cookies_data = []
    for row in requests_with_cookies.to_dict('records'):
        cookie = row['cookies']
        if len(cookie['blockedReasons']) == 0:
            datum = cookie['cookie'].copy()
            datum.update({'request_url': row['url'], 'site': site, 'page_url': page_url})
            # Avoid unhashable dict values.
            # like partitionKey: {'topLevelSite': 'https://parfois.com', 'hasCrossSiteAncestor': True}
            for k, v in datum.items():
                if isinstance(v, dict):
                    datum[k] = hashabledict(v)
            cookies_data.append(datum)
    sent_cookies = pd.DataFrame(
        cookies_data).drop_duplicates().reset_index(drop=True).to_dict('records')
    if verbose >= 3:
        print(har_dict, sent_cookies)
    return sent_cookies

def _contain_cookie(cookies: pd.DataFrame, consent_cookie: ConsentCookie, verbose=0):
    if len(cookies) == 0:
        return False
    characteristic_val = consent_cookie.get_characteristic_val()
    found = cookies[(cookies.path == consent_cookie.cookie['path']) & (cookies.name == consent_cookie.cookie['name']) & (cookies.domain == consent_cookie.cookie['domain']) & (cookies.value.str.contains(characteristic_val))]
    if verbose >= 3:
        print(f'{consent_cookie.cookie=}')
        print(f'{characteristic_val=}')
    return len(found) > 0


def is_cookie_file_valid(sent_brcookies, page_url: str, consent_cookie: ConsentCookie, postrej_cookies_file, verbose=3):
    if not url_domain_match(page_url, consent_cookie.cookie['domain'], consent_cookie.cookie['path']):
        if verbose >= 2: print(f"Unmatch url and consent cookie domain: {page_url=} {consent_cookie.cookie['domain']=} {consent_cookie.cookie['path']=} {postrej_cookies_file.parent.name}/{postrej_cookies_file.name}")
        return False

    # Do not check contain cookie if the consent cookie is in the local storage.
    if consent_cookie.local_storage_key == '' and not _contain_cookie(sent_brcookies, consent_cookie):
        if verbose >= 2: print(f"Post rej cookie not contain consent cookie, {postrej_cookies_file.parent.name}/{postrej_cookies_file.name} not have cookie {consent_cookie.cookie['name']} of {consent_cookie.cookie['domain']} on path {consent_cookie.cookie['path']}")
        return False

    return consent_cookie is not None

SENT_PREFIX = 'sent_'

def get_page_url(har_dict, verbose=2):
    pages = har_dict['log']['pages']
    if verbose >= 2 and len(pages) != 1: print(f"WARNING: Unexpected number of pages in har: {len(pages)}")
    return pages[0]['url']

def read_postrej_sent_cookies_from_file(postrej_cookies_file: Path, consent_cookie: ConsentCookie, verbose=0):
    """Map sent cookies to browser cookies and return them."""
    if verbose >= 3: print(f"Process {postrej_cookies_file.name}")
    # try:
    #     postrej_info_file = postrej_cookies_file.parent / (postrej_cookies_file.name.replace('.har.xz', '_cookies.json'))
    #     postrej_info = json.loads(postrej_info_file.read_text())
    # except Exception as e:
    #     print(f"Error loading cookie for site {postrej_info_file.parent.name}/{postrej_info_file.name}: {e}")
    #     return None

    har_dict = load(str(postrej_cookies_file))
    page_url = get_page_url(har_dict)
    site = postrej_cookies_file.parent.name
    sent_brcookies = get_sent_cookies(har_dict, site, page_url)
    sent_brcookies = set([hashabledict(cookie) for cookie in sent_brcookies])

    # Validate the data.
    if not is_cookie_file_valid(pd.DataFrame(sent_brcookies), page_url, consent_cookie, postrej_cookies_file):
        if verbose >= 3: print(f"WARNING: {postrej_cookies_file} invalid")
        return None

    return sent_brcookies

def get_consent_cookie(site_dir, verbose=2):
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
        return None

    consent_lib_name = log['scan_result']['consent_lib_name']
    consent_cookie_cls = ConsentLibFactory.get_consent_cookie_class_by_name(consent_lib_name)

    if consent_lib_name == 'termly':
        return consent_cookie_cls({}, domain=get_suffixed_domain_with_dot_prefix(brcookies_info['url']))

    consent_cookie_dict = find_cookie_in_page_cookies(
        brcookies_info['browser_cookies'], brcookies_info['url'], consent_cookie_cls.consent_cookie_name, warnings=None)
    if consent_cookie_dict is None:
        if verbose >= 2: print(f"Cannot get consent cookie for {site_dir}")
        return None

    return consent_cookie_cls(consent_cookie_dict)

def read_site_dir(site_dir: Path, file_pattern: str, verbose=2):
    if verbose >= 3:
        print("Read site dir", site_dir)
    consent_cookie = get_consent_cookie(site_dir)
    if consent_cookie is None:
        return None

    sent_cookies = []
    for har_file in site_dir.glob(file_pattern):
        try:
            cookies = read_postrej_sent_cookies_from_file(har_file, consent_cookie)
            if cookies is not None:
                sent_cookies.extend(cookies)
        except Exception as e:
            if verbose >= 2: print(f'Error reading har file {har_file}:', e)
    # return pd.concat(sent_cookies_dfs) if sent_cookies_dfs else None
    return pd.DataFrame(sent_cookies) if sent_cookies else None


def read_scan_dir(scan_dir: Path, file_pattern: str):
    assert file_pattern.endswith(
        'har.xz'), f"Unsupported file format; support only har now."
    dfs = []
    scan_dirs = list(scan_dir.glob('*'))
    for site_dir in scan_dirs: # tqdm(scan_dirs[:100]):
        # if site_dir.name not in ['tcs.com', 'unilever.com']: continue   ## Test
        site_df = read_site_dir(site_dir, file_pattern)
        if site_df is not None:
            dfs.append(site_df)
    return pd.concat(dfs)


def read_postrej_sent_cookies_in_scans(scan_dirs: List[Path], postrej=True) -> pd.DataFrame:
    file_pattern = 'postrej*.har.xz' if postrej else 'prerej*.har.xz'
    dfs = [read_scan_dir(scan_dir, file_pattern) for scan_dir in scan_dirs]
    return pd.concat(dfs)


def read_postrej_cookies(location='us'):
    scan_dirs = [get_data_dir2_by_location(location) / 'test_scan']
    print("Scan dirs:", scan_dirs)
    df = read_postrej_sent_cookies_in_scans(scan_dirs)
    # scan_root_dir = get_scan_root_dir(location)
    # out_file = scan_root_dir / 'scan.parquet'
    # df.to_parquet(out_file); print(f"Written to {out_file}")


def read_postrej_cookies_termly():
    scan_dirs = [get_data_dir('2022-05-30/termly')]
    # scan_dirs = get_scan_dirs(location)
    # scan_root_dir = get_scan_root_dir(location)
    df = read_postrej_sent_cookies_in_scans(scan_dirs)
    # out_file = scan_root_dir / 'scan.parquet'
    # df.to_parquet(out_file); print(f"Written to {out_file}")

def test_prerej_reader():
    scan_dirs = [get_data_dir('2021-12-15') / 'pref_menu_scan']
    df = read_postrej_sent_cookies_in_scans(scan_dirs, postrej=False)
    print(df)

if __name__ == '__main__':
    # read_postrej_cookies('us')
    read_postrej_cookies('toronto')
    # read_postrej_cookies_termly()
    # test_prerej_reader()
    print("Test passed.")
