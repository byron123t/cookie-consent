from pathlib import Path
import json

import pandas as pd

from consent.cmp.consentlib.consent_resource.resource import ConsentResource
from consent.cmp.consentlib.consent_resource.factory import ConsentResourceFactory
from consent.cmp.consentlib.consent_resource.onetrust import EnJsonOneTrustResource, ConsentJsOneTrustResource
from consent.cmp.consentlib.consent_resource.cookiebot import CcJsCookiebotResource
from consent.cmp.consentlib.consent_cookie import ConsentCookie
from consent.cmp.consentlib.factory import ConsentLibFactory
from consent.cmp.consentlib.onetrust import OptanonConsentCookie
from consent.cmp.consentlib.cookiebot import CookiebotConsentCookie
from consent.cmp.consentlib.termly import TermlyApiCacheLocalStorage
from ooutil.url_util import get_suffixed_domain

lib_name_map = {
    'cookiebot': 'cookiebot_new'
}

termly_sites = ['eskill.com']

def read_termly_prefs(har_file: Path):
    local_stor_file = har_file.parent / (har_file.stem + '.local_storage.json')
    # print(f'Read {local_stor_file}')
    local_stor = json.loads(local_stor_file.read_text())
    return local_stor['TERMLY_COOKIE_CONSENT']['value']

class CookieResourceReader:
    @classmethod
    def legacy_read_cookie_decls(cls, har_df):
        requests = pd.DataFrame.from_records(har_df.request)
        en_json_idx = requests[requests.url.str.endswith(cls.consent_resource_cls.lib_name)].index
        responses = pd.DataFrame.from_records(har_df.response)
        en_json_str = responses.iloc[en_json_idx].content.iloc[0]['text']
        return EnJsonOneTrustResource.decode(en_json_str)


    @classmethod
    def read_cookie_prefs(cls, page_url, har_df, sent_cookies, har_file, verbose=0):
        site = get_suffixed_domain(har_file.stem)
        requests = pd.DataFrame.from_records(har_df.request)
        responses = pd.DataFrame.from_records(har_df.response)
        for request in requests.itertuples():
        # for response in responses.itertuples():
            consent_resource_cls = ConsentResourceFactory.get_class_from_url(page_url, request.url)
            if consent_resource_cls:
                lib_name = consent_resource_cls.lib_name
                consent_cookie_cls = ConsentLibFactory.get_consent_cookie_class_by_name(lib_name_map.get(lib_name, lib_name))
                if verbose >= 2: print(f'{site=} {consent_cookie_cls=}')
                if site in termly_sites:
                    consent_cookie_dict = read_termly_prefs(har_file)
                    consent_cookie = consent_cookie_cls(consent_cookie_dict, domain=site)
                else:
                    consent_cookie_dict = sent_cookies[sent_cookies.name == consent_cookie_cls.consent_cookie_name][['name', 'value', 'path', 'domain']].drop_duplicates()
                    consent_cookie_dict = consent_cookie_dict.iloc[-1]
                    consent_cookie = consent_cookie_cls(consent_cookie_dict)
                if verbose >= 2: print(consent_cookie_dict)

                if len(consent_cookie_dict) == 0:
                    print(f'Cannot get consent lib for {page_url}')
                    return None

                resource_dict = responses.iloc[request.Index]
                consent_resource = consent_resource_cls(resource_dict)
                # print(resource_dict['content'])
                return consent_resource.decode_and_normalize(resource_dict['content']['text']), consent_cookie
        return None


class OneTrustReader:
    consent_resouce_cls = EnJsonOneTrustResource
    consent_cookie_cls = OptanonConsentCookie

class OneTrustLegacyReader:
    consent_resource_name = ''
    consent_cookie_name = 'OptanonConsent'

def read_har(har_file: Path):
    har = json.loads(har_file.read_text())
    pages = har['log']['pages']
    assert len(pages) == 1, f'Support only 1 page, {har_file=}'
    page_url = pages[0]['title']
    return page_url, pd.DataFrame.from_records(har['log']['entries'])

def get_man_sent_cookies_from_df(har_df, verbose=0):
    if verbose >= 2: print(f"Number of entries: {len(har_df):,d}")
    requests = pd.DataFrame.from_records(har_df.request).explode('cookies')
    requests_with_cookies = requests[~requests.cookies.isna()]
    cookies_data = []
    for row in requests_with_cookies.to_dict('records'):
        datum = row['cookies']
        # if len(cookie.get('blockedReasons', [])) == 0: # datum = cookie['cookie'].copy()
        cookies_data.append(datum)
    return pd.DataFrame(cookies_data).drop_duplicates().reset_index(drop=True)

def get_site(har_file: Path):
    file_stem = har_file.stem
    if '_' in file_stem:
        file_stem = file_stem.split('_')[0]
    return get_suffixed_domain(file_stem)

def get_man_cookies_from_file(har_file: Path, verbose=0):
    page_url, har_df = read_har(har_file)
    site = get_site(har_file)
    if verbose >= 2: print(f'Process file {har_file.name}')
    sent_cookies = get_man_sent_cookies_from_df(har_df)
    cookie_prefs = CookieResourceReader.read_cookie_prefs(page_url, har_df, sent_cookies, har_file)
    if cookie_prefs is None:
        print(f"Failed to get resource from {har_file}")
        return None, None
    cookie_decls, consent_cookie = cookie_prefs
    cat_prefs = consent_cookie.get_cat_prefs()
    cookie_prefs = cookie_decls.merge(cat_prefs, on='category_id')
    cookie_prefs = cookie_prefs.rename(columns={'Name': 'name', 'Host': 'domain'})
    cookie_prefs['site'] = site
    sent_cookies['site'] = site

    return sent_cookies, cookie_prefs

def get_man_sent_cookies_in_dir(data_dir: Path):
    sent_cookie_dfs = []
    cookie_pref_dfs = []
    for har_file in data_dir.glob('*.har'):
        man_sent_cookies, man_cookie_prefs = get_man_cookies_from_file(har_file)
        sent_cookie_dfs.append(man_sent_cookies)
        cookie_pref_dfs.append(man_cookie_prefs)
    return pd.concat(sent_cookie_dfs), pd.concat(cookie_pref_dfs)

def remove_leading_dot(s):
    return s[1:] if s.startswith('.') else s

def well_match_man_pref(cookie, man_cookie_prefs, verbose=0):
    # Strict way ...
    # cookie_domains = [cookie['domain'], remove_leading_dot(cookie['domain'])]
    # found_prefs = man_cookie_prefs[(man_cookie_prefs['name'] == cookie['name']) & man_cookie_prefs['domain'].isin(cookie_domains)].drop_duplicates()
    def match_func(cookie_pref):
        return cookie_pref['name'] == cookie['name'] and cookie['domain'].endswith(cookie_pref['domain'])
    found_prefs = man_cookie_prefs[man_cookie_prefs.apply(match_func, axis=1)].drop_duplicates()

    if len(found_prefs) >= 1:
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

def get_well_abstain_consis(site, auto_complies, man_sent_cookies, man_cookie_prefs, vio_types):
    man_sent_cookies = man_sent_cookies[man_sent_cookies.site == site]
    man_cookie_prefs = man_cookie_prefs[man_cookie_prefs.site == site]
    auto_complies = auto_complies[auto_complies.site == site]
    well_match_dfs, unsent_dfs, abstain_dfs = [], [], []

    for consis_type in vio_types: # ['incorrect']: # , 'omit']: #, 'comply']:
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

def get_matches_and_abstains(sites, auto_complies, man_sent_cookies, man_cookie_prefs, vio_types):
    match_dfs, unsent_dfs, abstain_dfs = [], [], []
    for site in sites:
        well_matches, unsents, abstains = get_well_abstain_consis(site, auto_complies, man_sent_cookies, man_cookie_prefs, vio_types)
        match_dfs.append(well_matches), unsent_dfs.append(unsents), abstain_dfs.append(abstains)
    return pd.concat(match_dfs).reset_index(drop=True), pd.concat(unsent_dfs).reset_index(drop=True), pd.concat(abstain_dfs).reset_index(drop=True)