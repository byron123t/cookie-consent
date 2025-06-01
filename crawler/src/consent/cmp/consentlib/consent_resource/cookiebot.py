#%%
from ast import literal_eval
import re
from typing import List

import pandas as pd

from consent.cmp.consentlib.consent_resource.resource import MALFORM_RESP, ConsentResource, COOKIE_LIST_COLS


# Modified Source code from Bollinger https://bit.ly/3iwNbg1
# LICENSE: https://github.com/dibollinger/CookieBlock-Crawler-Prototype/blob/main/LICENSE
# patterns to parse the final cc.js file, which is where the actual category data is stored
category_to_pattern = {"necessary": re.compile("CookieConsentDialog\\.cookieTableNecessary = (.*);"),
                       "preferences": re.compile("CookieConsentDialog\\.cookieTablePreference = (.*);"),
                       "statistics": re.compile("CookieConsentDialog\\.cookieTableStatistics = (.*);"),
                       "marketing": re.compile("CookieConsentDialog\\.cookieTableAdvertising = (.*);"),
                       "unclassified": re.compile("CookieConsentDialog\\.cookieTableUnclassified = (.*);")}

reponse_mode_pattern = ";CookieConsent\.responseMode='([a-z]*)'"
from consent.cmp.consentlib.cookiebot import consent_categories
assert set(category_to_pattern.keys()) - set(['unclassified']) == set(consent_categories), f'{list(category_to_pattern.keys())=} contains some invalid cookie categories.'

REGION_BLOCK = "region_block"
LIBRARY_ERROR = "library_error"

def get_response_mode(js_contents):
    matchobj = re.search(reponse_mode_pattern, js_contents)
    if matchobj is None:
        return None

    return matchobj.group(1)

class CookiebotResource(ConsentResource):
    lib_name = 'cookiebot'
    domains = ['cookiebot.com']


class CcJsCookiebotResource(CookiebotResource):
    pattern_name = 'cc.js'
    url_path_pattern = r'\/cc.js$'

    @classmethod
    def check_js_contents(cls, js_contents):
        if "CookieConsent.setOutOfRegion" in js_contents:
            raise ValueError(
                f"{REGION_BLOCK} Received an out-of-region response")
        elif re.search("cookiedomainwarning='Error: .* is not a valid domain.", js_contents):
            raise ValueError(
                f"{LIBRARY_ERROR} Cookiebot doesn't recognize referer referer with cbid as a valid domain.")
        elif len(js_contents.strip()) == 0:
            raise ValueError(
                f"{LIBRARY_ERROR} Empty response when trying to retrieve JavaScript content.")

    @classmethod
    def decode(cls, js_contents: str, warnings=None):
        """Input: cc.js text content."""
        cls.check_js_contents(js_contents)

        response_mode = get_response_mode(js_contents)

        cookie_list = []
        # Finally, if we arrived here we likely found our cookie category data.
        try:
            for catname, category_pattern in category_to_pattern.items():
                matchobj = category_pattern.search(js_contents)
                if not matchobj:
                    if warnings:
                        warnings.append(
                            f"Could not find array for category {catname}")
                    continue

                tmp = matchobj.group(1).replace("null", '"null"')
                cookies: List[str] = literal_eval(tmp)
                for c in cookies:
                    for effective_domain in [c[1], c[7]]:
                        for domain in effective_domain.split('<br/>'): # c[1].split('<br/>')
                            cookie_list.append({'name': c[0],
                                                'domain': domain,
                                                'c6': c[6], # don't know, it is mostly empty
                                                # 'provider_domain': c[7],
                                                'purpose': c[2],
                                                'duration': c[3],
                                                'cookie_protocol': c[4],
                                                'storage_type': c[5],
                                                'category_id': catname,
                                                'category': catname,
                                                'consent_mode': response_mode
                                                })
        except Exception as e:
            raise ValueError(
                f"{MALFORM_RESP} Failed to extract cookie data from cc.js: {str(e)}")

        return pd.DataFrame(cookie_list)

    @classmethod
    def normalize(cls, raw_cookies: pd.DataFrame, verbose=0) -> pd.DataFrame:
        if verbose >=2: print(cls.lib_name, "normalize")
        return raw_cookies[COOKIE_LIST_COLS].copy()

def test():
    from consent.util.default_path import get_data_dir
    data_root_dir = get_data_dir('2021-08-09/pref_menu_scan')
    resource_file = data_root_dir / 'acm.org' / 'consent_resources.json'
    cookie_list = CcJsCookiebotResource.get_cookie_list_from_file(resource_file)
    assert len(cookie_list) > 0, f'Error getting cookie list for file {resource_file}'

    resource_file = data_root_dir / 'plesk.com' / 'consent_resources.json'
    cookie_list = CcJsCookiebotResource.get_cookie_list_from_file(resource_file)
    assert len(cookie_list) > 0, f'Error getting cookie list for file {resource_file}'

if __name__ == '__main__':
    from consent.util.default_path import get_data_dir, get_data_dir2
    test()
    print("Tests passed.")

# %%
    site = 'royal.uk'
    # resource_file = get_data_dir('2021-08-09/pref_menu_scan') / 'bankrate.com' / 'consent_resources.json'
    resource_file = get_data_dir2('2023-11-21/pref_menu_scan_0k_20k') / site / 'consent_resources.json'
    assert resource_file.exists()
    # resource_content = json.loads(json.loads(resource_file.read_text())[0]['response'])
    # resource_content['DomainData']['Groups']
    # resource_content
    # %%
    cookie_list = CcJsCookiebotResource.get_cookie_list_from_file(resource_file)
    assert len(cookie_list) > 0, f'Cannot get cookie list from file {resource_file}'
    print(cookie_list)

    # %%
    cookie_list

# %%
