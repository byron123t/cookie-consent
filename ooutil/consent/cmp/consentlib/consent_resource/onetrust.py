import json
from typing import List

import pandas as pd

from consent.cmp.consentlib.consent_resource.resource import ConsentResource, COOKIE_LIST_COLS

verbose = 0

class OneTrustResource(ConsentResource):
    lib_name = 'onetrust'
    domains: List[str] = []  # ignore domains
    resource_domains = ['onetrust.com', 'cookielaw.org', 'cookiepro.com',
               'optanon.blob.core.windows.net', 'cookiepro.blob.core.windows.net',
               'a.sfdcstatic.com', 'cdn-ukwest.onetrust.com']

class EnJsonOneTrustResource(OneTrustResource):
    """Represent en.json"""
    pattern_name = 'en.json'
    # url_path_pattern = r'\/consent\/[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}\/[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}\/en(-[a-z][a-z])?\.json$'
    url_path_pattern = r'\/[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}\/en(-[a-z][a-z])?\.json$'

    @classmethod
    def decode(cls, resource_content: str, warnings=None):
        response = json.loads(resource_content)  # the content is a json file
        domain_data = response['DomainData']
        groups = domain_data['Groups']
        group_cookies_list = []
        vendorid_to_cookies = cls._get_vendor_cookies(domain_data)
        for group in groups:
            group_cookies_dfs = [pd.DataFrame(
                group['FirstPartyCookies']), pd.json_normalize(group['Hosts'], 'Cookies')]

            for vendorid in group.get('GeneralVendorsIds', []):
                group_cookies_dfs.append(vendorid_to_cookies[vendorid])

            group_cookies = pd.concat(group_cookies_dfs)

            group_cookies['category'] = group['GroupName']
            group_cookies['category_id'] = group['OptanonGroupId']
            group_cookies['consent_mode'] = group['Status']

            group_cookies_list.append(group_cookies)

        cookies = pd.concat(group_cookies_list).reset_index(drop=True)
        if len(cookies) == 0:
            return None
        if verbose >= 2: print(cookies)
        cookies.Length = cookies.Length.astype(int)
        return cookies

    @classmethod
    def _get_vendor_cookies(cls, domain_data):
        vendorid_to_cookies = {}
        for vendor in domain_data.get('GeneralVendors', []):
            vendorid = vendor['VendorCustomId']
            if vendorid in vendorid_to_cookies:
                print(f"WARNING {vendorid} duplicates")
            vendorid_to_cookies[vendorid] = pd.DataFrame(vendor['Cookies'])
        return vendorid_to_cookies

    def normalize(self, raw_cookies: pd.DataFrame) -> pd.DataFrame:
        def get_duration(row):
            assert row['Length'] != 'Session'
            if row.IsSession:
                return 'Session' # Session is not in row Length
            return f"{row['Length']} days"
        if len(raw_cookies[(raw_cookies.IsSession == True) & (raw_cookies.Length != 0.0)]) > 0:
            print(f'{self._resource["url"]} WARNING: Cookie list has session cookie but duration > 0')
        cookies = raw_cookies.copy() # [['Name', 'Host', 'IsSession', 'Length', 'DurationType', 'category', 'category_id']].copy()
        cookies.rename(columns={'Name': 'name', 'Host': 'domain'}, inplace=True)
        cookies['duration'] = cookies.apply(get_duration, axis=1)
        return cookies[COOKIE_LIST_COLS]


class ConsentJsOneTrustResource(OneTrustResource):
    """Represent consent.js"""
    pattern_name = 'consent_js'
    url_path_pattern = r'\/consent\/[-a-zA-Z0-9]*.js$'
