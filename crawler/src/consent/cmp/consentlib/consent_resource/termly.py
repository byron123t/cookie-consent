# %%
from typing import List
import json

import pandas as pd

from consent.cmp.consentlib.consent_resource.resource import COOKIE_LIST_COLS, MALFORM_RESP, ConsentResource


class TermlyCookiesResource(ConsentResource):
    lib_name = 'termly'
    domains: List[str] = ['termly.io']
    pattern_name = 'cookies_json'
    url_path_pattern = r'\/documents\/[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}\/cookies$'

    @classmethod
    def decode(cls, resource_content: str, warnings=None, verbose=0):
        """Input: termly.io/.../cookies text content."""
        try:
            category_to_cookies = json.loads(resource_content)['cookies']
        except Exception as e:
            raise ValueError(
                f"{MALFORM_RESP} Failed to extract cookie data from cookies")

        cookies_dfs: List[pd.DataFrame]  = [pd.DataFrame(cookies) for cookies in category_to_cookies.values()]
        return pd.concat(cookies_dfs)

    @classmethod
    def normalize(cls, raw_cookies: pd.DataFrame, verbose=0) -> pd.DataFrame:
        if verbose >=2: print(cls.lib_name, "normalize")

        raw_cookies['duration'] = raw_cookies['expire']
        raw_cookies['category_id'] = raw_cookies['category']
        raw_cookies['consent_mode'] = None

        if verbose >= 2: print('Raw cookies:\n', raw_cookies)

        return raw_cookies[COOKIE_LIST_COLS].copy()

if __name__ == '__main__':
    pass
    import json
    from consent.util.default_path import get_data_dir
    resource_file = get_data_dir('2022-05-30/termly/termly.io/consent_resources.json')
    # SCAN_DIRS = list(SCAN_ROOT_DIR.glob('*'))
    # resource_file = get_data_dir('2021-08-13/pref_menu_scan_20k_30k/royalairmaroc.com') / 'consent_resources.json'
    resources = json.loads(resource_file.read_text())
    len(resources)
    result = TermlyCookiesResource.get_cookie_list_from_file(resource_file)
    result
# %%
    result
