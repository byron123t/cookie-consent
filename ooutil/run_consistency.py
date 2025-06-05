from collections import defaultdict
from pathlib import Path

import pandas as pd

from consent.consistency.comply_util import site_to_contras, get_comply
from consent.consistency.cookie_pref_match import cookie_pref_match
from consent.consistency.util import get_scan_root_dir, get_scan_dirs # , FIG_DIR uncomment to save fig.
from consent.data.pref_menu_scan.cookie_pref_reader import read_cookie_prefs_in_scans
from consent.data.pref_menu_scan.har_cookie_reader import read_postrej_sent_cookies_in_scans
from consent.data.pref_menu_scan.har_cookie_reader import read_postrej_sent_cookies_in_scans
from pathlib import Path

LOCATION_TO_EXPER_DATE = {
    'za': '2024-10-12',
    'eu': '2024-10-11',
    'uk': '2024-10-06',
    'us': '2024-10-04',
    'sg': '2024-10-08',
    'au': '2024-10-07',
    'can': '2024-10-09',
    'ca': '2024-10-10',
}

# NEED TO UPDATE THIS TO WORK ON EACH BATCH OF SCANS MAYBE A FOR LOOP AND SOME DIFFERENT PATHING
cur_set = '0k_20k' # '20k_100k'
overwrite = True
# SCAN_ROOT_DIR = get_scan_root_dir('capetown')

for iteration in range(0, 10):
    for location, date in LOCATION_TO_EXPER_DATE.items():
        SCAN_ROOT_DIR = Path(f'data/{date}/')
        SCAN_DIRS = [SCAN_ROOT_DIR / f'pref_menu_scan_{cur_set}_{iteration}']
        SCAN_OUT_DIR = Path(f'data/regions/{location}')
        # SCAN_DIRS = get_scan_dirs('us')[:]
        output_suffix = '_' + cur_set # '0k_20k'  # '20k_100k' #'60k_80k' # '40k_60k' # # '100k_200k'; done: '20k_40k' '0k_20k'
        print('Scan root dir:', SCAN_ROOT_DIR)
        print('Output suffix:', output_suffix)
        print('Scan dirs:', SCAN_DIRS)

        # Get cookie prefs = cookie decls + prefs
        cookie_prefs_file = SCAN_OUT_DIR / f'cookie_prefs{output_suffix}_{iteration}.parquet'

        if not cookie_prefs_file.exists() or overwrite:
            save_cookie_decls_file = SCAN_OUT_DIR / f'cookie_decls{output_suffix}_{iteration}.parquet'
            print(f'To save to {save_cookie_decls_file}')
            cookie_prefs = read_cookie_prefs_in_scans(SCAN_DIRS, save_cookie_decls_file)  # took 2.3min for top 50k-site scan
            cookie_prefs.to_parquet(cookie_prefs_file); print(f'Written to {cookie_prefs_file}')
        else:
            cookie_prefs = pd.read_parquet(cookie_prefs_file)
        cookie_prefs.head()

        print("Found cookie libraries:")
        cookie_prefs[['site', 'lib_name']].drop_duplicates().lib_name.value_counts()

        cookielist_sites = sorted(cookie_prefs.site.unique().tolist())
        n_cookielist_sites = len(cookielist_sites)
        assert cookie_prefs.site.nunique() == n_cookielist_sites
        n=10
        print("Sites with cookie prefs:", n_cookielist_sites, f', first {n} sites:' , cookielist_sites[:n])

        site_to_libname = {row['site']: row['lib_name'] for row in cookie_prefs[['site', 'lib_name']].drop_duplicates().to_dict('records')}

        print(len(cookie_prefs[cookie_prefs.name.str.endswith('#')]) / len(cookie_prefs))
        print(len(cookie_prefs[cookie_prefs.name.str.endswith('xxx')]) / len(cookie_prefs))
        print(len(cookie_prefs[cookie_prefs.name.str.endswith('XXX')]) / len(cookie_prefs))
        cookie_prefs[cookie_prefs.name.str.endswith('#')]


        cookies_cache_file = SCAN_OUT_DIR / f'scan{output_suffix}_{iteration}.parquet'  # 'raw_postrej_sent_cookies.parquet'

        if not cookies_cache_file.exists() or overwrite:
            sent_cookies = read_postrej_sent_cookies_in_scans(SCAN_DIRS)
            if cookies_cache_file: sent_cookies.to_parquet(cookies_cache_file); print(f"Written to {cookies_cache_file}")
        else:
            sent_cookies = pd.read_parquet(cookies_cache_file)

        print(f"Number sent cookies read: {len(sent_cookies):,d}")
        sent_cookies.head(3)

        prj_sent_cookies = sent_cookies[['name', 'domain', 'path', 'site']].drop_duplicates()

        sites = set(cookie_prefs.site)
        print(f"Num sent cookies in the cookie prefs sites: {len(prj_sent_cookies[prj_sent_cookies.site.isin(sites)]):,d}")

        import sys; import importlib; importlib.reload(sys.modules['consent.consistency.comply_util'])
        from consent.consistency.comply_util import get_comply

        print("faster: for cookie_pref in cookie_pref_set[cookie_pref_set.name == acookie['name']]:")
        all_complies = get_comply(cookie_prefs, prj_sent_cookies)
        all_complies.head()

        complies = all_complies[['name', 'domain', 'path', 'site', 'comply']].drop_duplicates()
        comply_sites_data = defaultdict(list)
        for comply_type, comply_group in complies.groupby('comply'):
            n_sites = comply_group.site.nunique()
            comply_sites_data['comply_type'].append(comply_type)
            comply_sites_data['num_sites'].append(n_sites)
            comply_sites = pd.DataFrame(comply_sites_data).sort_values(by=['num_sites'], ascending=False)

        nsites = all_complies.site.nunique()
        comply_counts = complies.comply.value_counts()
        comply_sites['num_sites_percent'] = comply_sites['num_sites'] / nsites * 100
        comply_sites['num_cookies'] = comply_sites['comply_type'].map(comply_counts)
        comply_sites['num_cookies_percent'] = comply_sites['num_cookies'] / comply_sites['num_cookies'].sum() * 100  # need to read scan_*.parquet for n_br_cookies, but may be unnecessary
        comply_sites['num_cookies_per_site'] = comply_sites['num_cookies'] / comply_sites['num_sites']

        # Do not count comply/correct enforcement: which require detecting all possible
        comply_sites = comply_sites[comply_sites.comply_type != 'comply']
        comply_sites

        all_complies_file = SCAN_OUT_DIR / f'all_complies{output_suffix}_{iteration}.parquet'
        all_complies.to_parquet(all_complies_file); print(f"Written {len(all_complies):,d} records of all_complies to {all_complies_file}")

        nsites = all_complies.site.nunique(); nsites

        detected_contra_sites = [s for s, contras in site_to_contras.items() if len(contras) > 0]; len(detected_contra_sites)

        complies = all_complies[ ['name', 'domain', 'site', 'comply',]].drop_duplicates()
        comply_counts = complies.comply.value_counts()

        complies_sites = set(all_complies.site)
        sent_cookies_com = sent_cookies[sent_cookies.site.isin(complies_sites)]
        prj_sent_cookies_com = sent_cookies_com[['domain', 'expires', 'name', 'path', 'sameSite', 'secure', 'value', 'request_url', 'site']].drop_duplicates()
        prj_br_cookies_com = prj_sent_cookies_com[['domain', 'expires', 'name', 'path', 'sameSite', 'secure', 'site']].drop_duplicates()
        print(f"Num captured sent cookies: {len(sent_cookies_com):,d}")
        print(f"Num unique captured cookies: {len(prj_sent_cookies_com):,d}")

        n_br_cookies_com = len(prj_br_cookies_com)
        print(f"Num unique browser cookies: {n_br_cookies_com:,d} on {prj_br_cookies_com.site.nunique():,d} websites") # and {sent_cookies.page_url.nunique():,d} pages")

        # Way 1: compute contra sites by dynamic analysis: this should be lower than statically analyzing prefs
        # because we cannot check all combinations of consent modes.
        from consent.consistency.comply_util import get_appr_rej_sets
        contra_data = []
        for asite in cookie_prefs.site.unique():
            site_prefs = cookie_prefs[cookie_prefs.site == asite]
            _, _, contras = get_appr_rej_sets(site_prefs)
            for contra in contras:
                contra['site'] = asite
                contra_data.append(contra)
        contra_sites = pd.DataFrame(contra_data)
        contra_sites.head()

        set(detected_contra_sites) - set(contra_sites.site)
        set(contra_sites.site) - set(detected_contra_sites)

        contra_cookies_dfs = []
        for _, same_cookies in cookie_prefs.groupby(['name', 'domain', 'site']):
            consent_modes = same_cookies.consent_mode.unique()
            if len(consent_modes) >= 2 and same_cookies.category.nunique() > 1: # and 'always active' in consent_modes:
                contra_cookies_dfs.append(same_cookies)
        contra_cookies = pd.concat(contra_cookies_dfs).drop_duplicates()