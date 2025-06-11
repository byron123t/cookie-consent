# %%
"""Read cookie-category preferences."""

from pathlib import Path
import json
from typing import List

from colorama import Fore
import pandas as pd

from consent.cmp.consentlib.factory import ConsentLibFactory
from src.ooutil.cookie_store import CookieStore


def read_cat_prefs_in_dir(site_dir: Path, verbose=2):
    if verbose >= 3: print(site_dir)
    log_file = site_dir / 'log.json'
    if not log_file.exists():
        return None
    site = site_dir.name
    try:
        log = json.loads(log_file.read_text())
    except Exception as e:
        raise ValueError(f'Fail to read log file {site_dir.name} corrupted: {e}')
    if log['error'] is not None:
        return None
    scan_result = log['scan_result']
    consent_lib_name = scan_result['consent_lib_name']
    cookie_class = ConsentLibFactory.get_consent_cookie_class_by_name(consent_lib_name) #, verbose=0)
    if cookie_class is None:
        raise ValueError(f"Cannot get cookie class for {site_dir}")

    if consent_lib_name == 'termly':
        cat_prefs_file = site_dir / 'postrej_0_consent_state.json'
        cat_prefs_dict = json.loads(cat_prefs_file.read_text())
        cat_prefs = pd.DataFrame(cat_prefs_dict.items(), columns=['category_id', 'consent'])
    else:
        postrej_cookies_file = site_dir / 'postrej_0_cookies.json'
        try:
            postrej_cookies = json.loads(postrej_cookies_file.read_text())
        except Exception as e:
            raise ValueError(f'Fail to read post-rejection cookie file {site_dir.name} corrupted: {e}')
        cookie_store = CookieStore(postrej_cookies['browser_cookies'], postrej_cookies['url'])
        found_cookies = cookie_store.find_cookies_in_page(cookie_class.consent_cookie_name)
        if len(found_cookies) > 1:
            print(f'WARNING: Found non-unique (not found or >1 instance) {site_dir.name}')
        if len(found_cookies) == 0:
            print(f'WARNING: Consent cookie not found {site_dir.name}')
            return None
        consent_cookie = cookie_class(found_cookies.iloc[0])

        try:
            cat_prefs = consent_cookie.get_cat_prefs()
        except Exception as e:
            print(f'WARNING: Error reading cat prefs:', e)
            return None

    cat_prefs['site'] = site
    return cat_prefs


def read_cat_prefs_in_dirs(site_dirs: List[Path]):
    cat_prefs_dfs = []
    fail_sites = []
    for site_dir in site_dirs:
        try:
            cat_prefs = read_cat_prefs_in_dir(site_dir)
            if cat_prefs is not None:
                cat_prefs_dfs.append(cat_prefs)
        except ValueError as e:
            print(f"Error reading {site_dir.name} {e}")
            fail_sites.append(site_dir.name)

    if fail_sites:
        print(Fore.RED + f"Fail to read log {len(fail_sites)} sites:", fail_sites, Fore.RESET)
    return pd.concat(cat_prefs_dfs)


def test():
    from consent.util.default_path import get_data_dir
    data_root_dir = get_data_dir('2021-08-12/pref_menu_scan')
    site_dirs = data_root_dir.glob('*')
    # df, _, _ = read_cat_prefs_in_dirs(site_dirs)
    # print(df)


# if __name__ == '__main__':
    # test()
    # %%

    from consent.util.default_path import get_data_dir
    # data_root_dir = get_data_dir('2021-08-12/pref_menu_scan')
    data_root_dir = get_data_dir('2022-05-30')
    site_dirs = list(data_root_dir.glob('termly/*'))

    cat_prefs = read_cat_prefs_in_dirs(site_dirs)
    print(f"Num category-preferences: {len(cat_prefs):,d}")
    cat_prefs.head()

# %%
    len(set(['oracle.com', 'ibm.com', 'proquest.com', 'churchofjesuschrist.org', 'logmein.com', 'zimbra.com', 'formula1.com', 'logmein.com', 'exlibrisgroup.com', 'blackberry.com', 'trulia.com', 'cntraveler.com', 'opendns.com', 'broadcom.com', 'hotjar.com', 'salesforce.com', 'ulta.com', 'adobe.com', 'pendo.io', 'glassdoor.com', 'bankrate.com', 'jobvite.com', 'mlb.com', 'accenture.com', 'thomsonreuters.com', 'hindawi.com', 'sketchup.com', 'akamai.com', 'mcdonalds.com', 'rte.ie', 'bodybuilding.com', 'askubuntu.com', 'seagate.com', 'klarna.com', 'tfl.gov.uk', 'prnewswire.com', 'bazaarvoice.com', 'commonsensemedia.org', 'digitalspy.com', 'people.com', 'dictionary.com', 'hbomax.com', 'allure.com', 'instyle.com', 'freep.com', 'uab.edu', 'zapier.com', 'oxfordlearnersdictionaries.com', 'hltv.org', 'comodoca.com', 'fully-kiosk.com', '10fastfingers.com', 'quovadisglobal.com', 'openweathermap.org', 'ccleaner.com', 'liveperson.com', 'gfk.com', 'gunbroker.com', 'avast.com', 'fsc.org', 'app.com', 'bluejeans.com', 'dccomics.com', 'ralphlauren.com', 'plesk.com']))
    # len(set(site_dir.name for site_dir in site_dirs))

# %%
