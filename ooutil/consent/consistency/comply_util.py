from collections import defaultdict
from multiprocessing import Pool

from tqdm import tqdm
import pandas as pd

from ooutil.dict_util import hashabledict

module = 'consent.consistency.cookie_pref_match'
import sys
if module in sys.modules:
    import importlib; importlib.reload(sys.modules[module])
from consent.consistency.cookie_pref_match import cookie_pref_match

# Map intercepted cookies to browser cookies.

site_to_contras = {}  # TODO: make this to non-global one.
COOKIE_THRES = 3000

def check_in_set(site, acookie, cookie_pref_set, verbose=0):
    if len(cookie_pref_set) > COOKIE_THRES: # petsmart.com has 18k (incl. test cookies) hangs this check, 10 other sites have 2100 cookies
        print('Big cookie pref', site, len(cookie_pref_set), '...')
        # return False

    # check_url_host_match = relax_check_url_host_match # strict_check_url_host_match
    for cookie_pref in cookie_pref_set:
        if verbose >= 3:
            print(f'{cookie_pref=} {acookie=}')
        elif verbose >= 2:
            if cookie_pref['name'] == acookie['name']:
                print(f'{cookie_pref=} {acookie=}')

        if cookie_pref_match(acookie, cookie_pref, site):
            return True
    return False


def comply_check(site, acookie, appr_set, rej_set):
    is_appr = check_in_set(site, acookie, appr_set)
    is_rej = check_in_set(site, acookie, rej_set)
    if is_appr and not is_rej:
        return 'comply'
    elif not is_appr and is_rej:
        return 'incorrect'
    elif not is_appr and not is_rej:
        return 'omit'
    else:
        return 'ambiguous'


def get_appr_rej_sets(prefs):
    """Return 2 sets: appr and rejection."""
    def get_hashable_cookie_set(df):
        cookies = df[['domain', 'name']].to_dict('records')
        return set(hashabledict(c) for c in cookies)

    appr_set = get_hashable_cookie_set(prefs[prefs.consent == True])
    rej_set = get_hashable_cookie_set(prefs[prefs.consent == False])
    assert len(prefs[~prefs.consent.isin([True, False])]) == 0, prefs[~prefs.consent.isin([True, False])]

    contra_set = appr_set.intersection(rej_set)

    return appr_set, rej_set, contra_set


def _get_comply_for_site(site, prefs, sent_cookies, verbose=0):
    appr_set, rej_set, contra_set = get_appr_rej_sets(prefs)
    comply_results = []
    for sent_cookie in sent_cookies:
        comply = comply_check(site, sent_cookie, appr_set, rej_set)
        comply_result = sent_cookie.copy()
        comply_result.update({'comply': comply, 'site': site})
        comply_results.append(comply_result)
    if len(contra_set) > 0:
        site_to_contras[site] = contra_set
        if len(site_to_contras) < 20: # Print some of the contra to see the progress only
            if verbose >= 2: print(f'Contradictory set: {site=} {contra_set=}')
    return comply_results

def get_comply_for_sites(args, sites, parallel=False):
    if parallel: # not work, maybe bottleneck is the transfer of a big data frame.
        pool = Pool(32)
        for result in pool.starmap(_get_comply_for_site, args):
            yield result
    else:
        for arg in tqdm(args, total=len(sites)):
            yield _get_comply_for_site(*arg)

def get_compute_args(sites, cookie_prefs, prj_sent_cookies):
    #     return [(site, cookie_prefs, prj_sent_cookies) for site in sites]
    for site in sites:
        site_cookie_prefs = cookie_prefs[cookie_prefs.site == site]
        if len(site_cookie_prefs) > COOKIE_THRES: # petsmart.com has 18k (incl. test cookies) hangs this check
            print('Big cookie pref', site, len(site_cookie_prefs), 'skip this site')
            continue
        site_prj_sent_cookies = prj_sent_cookies[prj_sent_cookies.site == site].to_dict('records')
        yield site, site_cookie_prefs, site_prj_sent_cookies

def get_comply(cookie_prefs, prj_sent_cookies):
    sites = cookie_prefs.site.unique() # .tolist()
    #     sites = ['suse.com', 'ulta.com', 'optimizely.com', 'cell.com']
    args = get_compute_args(sites, cookie_prefs, prj_sent_cookies)

    comply_results = []
    for complies_for_site in get_comply_for_sites(args, sites, parallel=False):
        comply_results.extend(complies_for_site)

    return pd.DataFrame(comply_results)

def remove_leading_dot(s):
    return s[1:] if s.startswith('.') else s

def well_match_man_pref(cookie, man_cookie_prefs, verbose=0):
    cookie_domains = [cookie['domain'], remove_leading_dot(cookie['domain'])]
    found_prefs = man_cookie_prefs[(man_cookie_prefs['name'] == cookie['name']) & man_cookie_prefs['domain'].isin(cookie_domains)].drop_duplicates()

    if len(found_prefs) == 1:
        found_pref = found_prefs.iloc[0]
        consent = found_pref['consent']
        if not consent:
            return True
        elif verbose >= 3:
            print("Consent"); print(found_prefs)
    elif verbose >= 2:
        print("not found")
        print(found_prefs)
        print(cookie)
    return False

def exist_in_man_sent(cookie, man_sent_cookies):
    match_man_sent = man_sent_cookies[(man_sent_cookies['name'] == cookie['name']) & (man_sent_cookies['domain'] == cookie['domain']) & (man_sent_cookies['path'] == cookie['path'])]
    return len(match_man_sent) > 0

def check_detected_cookies(detected_cookies, man_sent_cookies, man_cookie_prefs):
    well_matches, unsents, abstains = [], [], []
    for cookie in detected_cookies.to_dict('records'):
        if exist_in_man_sent(cookie, man_sent_cookies):
            if well_match_man_pref(cookie, man_cookie_prefs):
                well_matches.append(cookie)
            else:
                abstains.append(cookie)
        else:
            unsents.append(cookie)
    return pd.DataFrame(well_matches), pd.DataFrame(unsents), pd.DataFrame(abstains)

def get_well_abstain_consis(site, auto_complies, man_sent_cookies, man_cookie_prefs):
    man_sent_cookies = man_sent_cookies[man_sent_cookies.site == site]
    man_cookie_prefs = man_cookie_prefs[man_cookie_prefs.site == site]
    auto_complies = auto_complies[auto_complies.site == site]
    well_match_dfs, unsent_dfs, abstain_dfs = [], [], []

    for consis_type in ['incorrect']: # , 'omit']: #, 'comply']:
        auto_cookies = auto_complies[auto_complies['comply'] == consis_type][['name', 'domain', 'path']].drop_duplicates().reset_index(drop=True)
        well_matches, unsents, abstains = check_detected_cookies(auto_cookies, man_sent_cookies, man_cookie_prefs)

        well_match_dfs.append(well_matches)
        unsent_dfs.append(unsents)
        abstain_dfs.append(abstains)

    well_match_df = pd.concat(well_match_dfs)
    unsent_df = pd.concat(unsent_dfs)
    abstain_df = pd.concat(abstain_dfs)
    well_match_df['site'] = site
    unsent_df['site'] = site
    abstain_df['site'] = site
    return well_match_df, unsent_df, abstain_df

def get_matches_and_abstains():
    match_dfs, unsent_dfs, abstain_dfs = [], [], []
    for site in sites:
        well_matches, unsents, abstains = get_well_abstain_consis(site, auto_complies, man_sent_cookies, man_cookie_prefs)
        match_dfs.append(well_matches), unsent_dfs.append(unsents), abstain_dfs.append(abstains)
    return pd.concat(match_dfs).reset_index(drop=True), pd.concat(unsent_dfs).reset_index(drop=True), pd.concat(abstain_dfs).reset_index(drop=True)