# %%
"""Read site cookie prefs in pref menu scan."""

from pathlib import Path
from typing import List, Optional

import pandas as pd

from consent.data.pref_menu_scan.cat_pref_reader import read_cat_prefs_in_dirs
from consent.data.pref_menu_scan.cookie_decl_reader import read_cookie_decls_in_dirs


def get_cookie_prefs(cat_prefs: pd.DataFrame, cookie_decl: pd.DataFrame, verbose=0):
    def get_consent(row, verbose=0):
        consent = site_cat_to_pref.get((row.site, row.category_id))
        if consent is None and verbose >= 2: print(f'WARNING: site {row.site} category {row.category_id} not exist.')
        return consent

    site_cat_to_pref = {}
    for row in cat_prefs.itertuples():
        site_cat_to_pref[(row.site, row.category_id)] = row.consent

    if verbose >= 3:
        print(f'{cat_prefs=}')
        print(f'{cookie_decl=}')

    if verbose >= 2 and len(cat_prefs) > 0 and len(cookie_decl) > 0:
        diff_sites = set(cookie_decl.site) - set(cat_prefs.site)
        print("Different between cookie-list and cat-pref sites cookie_decl.site - cat_prefs.site:", len(diff_sites), diff_sites)

    if len(cookie_decl) == 0:
        print("Warning: empty cookie_decl")
        return cookie_decl

    result = cookie_decl[cookie_decl.site.isin(cat_prefs.site)].copy()
    result['consent'] = result.apply(get_consent, axis=1)
    return result.dropna(subset=['consent'])


def read_cookie_prefs_in_dirs(site_dirs: List[Path], save_cookie_decls_file: Optional[Path]=None):
    def escape_surrogates(text: str):
        # From https://github.com/cloud-gov/pages-build-container/pull/100/files
        '''
        Escapes invalid surrogates in a unicode string.
        >>> escape_surrogates('agency’s.html')
        'agency’s.html'
        from http://lucumr.pocoo.org/2013/7/2/the-updated-guide-to-unicode/
        '''
        encoded = text.encode('utf-8', 'replace') # encode('utf-8', 'escapesurrogate') not work
        return encoded.decode('utf-8')

    cat_prefs = read_cat_prefs_in_dirs(site_dirs)
    cookie_decls = read_cookie_decls_in_dirs(site_dirs)
    if save_cookie_decls_file is not None:
        # Fix error of encoding column 'name'.
        cookie_decls['name'] = cookie_decls['name'].map(escape_surrogates)
        cookie_decls.to_parquet(save_cookie_decls_file)
        # write_df_to_file(cookie_decls, save_cookie_decls_file)

    return get_cookie_prefs(cat_prefs, cookie_decls)


def read_cookie_prefs_in_scans(scan_dirs: List[Path], save_cookie_decls_file: Optional[Path]=None):
    site_dirs = [site_dir for scan_dir in scan_dirs for site_dir in scan_dir.glob('*') if site_dir.is_dir()]
    assert all(d.is_dir() for d in site_dirs)
    return read_cookie_prefs_in_dirs(site_dirs, save_cookie_decls_file)


def test():
    from consent.util.default_path import get_data_dir
    data_root_dir = get_data_dir('2021-08-09/pref_menu_scan')
    site_dirs = [adir for adir in data_root_dir.glob('*') if adir.is_dir()]
    print(f"Num site dirs: {len(site_dirs)}")
    cookie_prefs = read_cookie_prefs_in_dirs(site_dirs)
    print(cookie_prefs.head())


if __name__ == '__main__':
    # test()
    # print("Tests passed.")
    pass
    # %%

    from consent.util.default_path import get_data_dir

    SCAN_ROOT_DIR = Path('/mnt/sda/ducbui/Dropbox/Dropbox (University of Michigan)/projects/data_sync/consent/2022-05-30/termly')
    site_dirs = list(SCAN_ROOT_DIR.glob('*'))

    sites = [adir.name for adir in site_dirs]
    print(f"Num site dirs: {len(site_dirs)}")
    cookie_prefs = read_cookie_prefs_in_dirs(site_dirs)
    cookie_prefs

    # %%
    cookie_prefs.lib_name.unique()

    # %%
    cookie_prefs[cookie_prefs.lib_name == 'cookiebot']

    # %%
    cat_prefs = read_cat_prefs_in_dirs(site_dirs)
    cookie_decl = read_cookie_decls_in_dirs(site_dirs)
    # %%

    def get_consent(row):
        print(row.site, row.category_id)
        return site_cat_to_pref[row.site, row.category_id]

    site_cat_to_pref = {}
    for row in cat_prefs.itertuples():
        site_cat_to_pref[(row.site, row.category_id)] = row.consent

    diff_sites = set(cookie_decl.site) - set(cat_prefs.site)
    print("Diff sites cookie list", len(diff_sites), diff_sites)

    cookie_decl = cookie_decl[cookie_decl.site.isin(cat_prefs.site)]
    cookie_decl['consent'] = cookie_decl.apply(get_consent, axis=1)

    # %%
    site_cat_to_pref
    # %%
    cookie_decl

    # %%
    # for site in sites:
    site = sites[0]
    cat_prefs[cat_prefs.site == site]
    # %%
    site_list = cookie_decl[cookie_decl.site == site]
    site_list

    # %%
    cat_prefs

    # %%
    cookie_decl.head()

# %%
    site = 'cntraveler.com'
    cookie_decl[(cookie_decl['site'] == site) & (
        cookie_decl['category_id'] == 'C0001')]

# %%
    cat_prefs[cat_prefs.site == site]

# %%
