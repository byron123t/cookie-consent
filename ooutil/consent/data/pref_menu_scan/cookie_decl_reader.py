#%%
"""Read resource files."""

from pathlib import Path
import json
from typing import List
from multiprocessing import Pool
from colorama.ansi import Fore

import pandas as pd
from src.ooutil.df_util import expand_dict_col

from consent.cmp.consentlib.consent_resource.factory import ConsentResourceFactory
from consent.cmp.consentlib.consent_resource.resource import ConsentResource

from consent.cmp.consentlib.consent_resource.onetrust import EnJsonOneTrustResource
import sys; import importlib; importlib.reload(sys.modules['consent.cmp.consentlib.consent_resource.factory'])
import sys; import importlib; importlib.reload(sys.modules['consent.cmp.consentlib.consent_resource.onetrust'])
from consent.cmp.consentlib.consent_resource.factory import ConsentResourceFactory
from consent.cmp.consentlib.consent_resource.onetrust import EnJsonOneTrustResource


# def get_cookie_decl(site:str, cr: ConsentResource, verbose=2):
    # return cr.get_cookie_list()

def read_resource(resource, res_file, site, verbose=0):
    if verbose >= 2: print(f'Read resource {res_file}')
    lib_name = resource['lib_name']
    pattern_name = resource['pattern_name']
    cs_class = ConsentResourceFactory.get_class(lib_name, pattern_name)
    if cs_class is None:
        raise ValueError(f"Cannot get consent resource class for file {res_file} {lib_name=} {pattern_name=}")
    # cr = cs_class(resource) # cookie_decl = get_cookie_decl(site, cr)
    cookie_decl = cs_class(resource).get_cookie_list()
    if verbose >= 3: print(f'{resource=} {res_file=} {cookie_decl}')

    if cookie_decl is None:
        return None
    # print(cookie_decl)
    cookie_decl['site'] = site
    cookie_decl['lib_name'] = lib_name
    cookie_decl['pattern_name'] = pattern_name
    return cookie_decl

def read_cookie_decls(site:str, res_file: Path, verbose=2):
    if verbose >= 3: print(f'Read resources for site {site}')
    if res_file.stat().st_size == 2: print(f"File {site} {res_file.name} has no data");
    for resource in json.loads(res_file.read_text()):
        try:
            yield read_resource(resource, res_file, site)
        except Exception as e:
            if verbose >= 2: print(f"WARNING: error decoding {res_file}:", e)

def is_log_error(site_dir):
    try:
        log_file = site_dir / 'log.json'
        return json.loads(log_file.read_text()).get('error') is not None
    except Exception as e:
        pass
    return True


def read_site_dir(site_dir, verbose=2):
    cookie_decl_dfs = []
    failed_sites = []

    if not is_log_error(site_dir):
        try:
            for cookie_decl in read_cookie_decls(site_dir.name, site_dir / 'consent_resources.json'):
                if cookie_decl is not None:
                    cookie_decl_dfs.append(cookie_decl)
        except Exception as e:
            if verbose >= 2: print(f"Cannot get resources for site {site_dir.name}: {type(e)} {str(e)}")
            failed_sites.append(site_dir.name)
    return cookie_decl_dfs, failed_sites


def read_cookie_decls_in_dirs(site_dirs: List[Path], verbose=2):
    cookie_decl_dfs = []
    failed_sites = []
    pool = Pool(32)
    results = pool.map(read_site_dir, site_dirs)

    for acookie_decl_dfs, afailed_sites in results:
        cookie_decl_dfs.extend(acookie_decl_dfs)
        failed_sites.extend(afailed_sites)

    if verbose >= 1 and failed_sites: print(Fore.RED + f'Failed to read cookie declarations on {len(failed_sites)}: {sorted(failed_sites)}', Fore.RESET)
    if len(cookie_decl_dfs) == 0:
        return pd.DataFrame()

    return pd.concat(cookie_decl_dfs)


def read_cookie_decls_in_scans(scan_dirs: List[Path]):
    site_dirs = [site_dir for scan_dir in scan_dirs for site_dir in scan_dir.glob('*') if site_dir.is_dir()]
    site_dirs = site_dirs[:100]
    assert all(d.is_dir() for d in site_dirs)
    return read_cookie_decls_in_dirs(site_dirs)


def test():
    from consent.util.default_path import get_data_dir
    scan_dirs = [get_data_dir('2021-08-09/pref_menu_scan')]
    df = read_cookie_decls_in_scans(scan_dirs)
    print(df)


# if __name__ == '__main__':
    # test()
    # %%

    from consent.util.default_path import get_data_dir
    from consent.consistency.util import _CA_SCAN_DIRS
    SCAN_ROOT_DIR = Path('/mnt/sda/ducbui/Dropbox/Dropbox (University of Michigan)/projects/data_sync/consent/2022-05-30/')
    SCAN_DIRS = list(SCAN_ROOT_DIR.glob('termly'))
    # data_root_dir = get_data_dir('2021-08-12/pref_menu_scan_10k_20k')
    # site_dirs = data_root_dir.glob('*')
    # cookie_decls = read_cookie_decls_in_dirs(site_dirs)
    cookie_decls = read_cookie_decls_in_scans(SCAN_DIRS)
    # print(f"Num cookies: {len(cookie_decls):,d}, Num sites: {cookie_decls.site.nunique():,d}")
    cookie_decls.head()

# %%