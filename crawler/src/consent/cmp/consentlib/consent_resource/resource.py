# %%
from typing import Dict, List, Optional, Type

import pandas as pd

from ooutil.df_util import find_one
from ooutil.url_util import get_suffixed_domain, match_resource_paths


def has_same_suffixed_domain(url, hostname):
    return get_suffixed_domain(url) == get_suffixed_domain(hostname)


COOKIE_LIST_COLS = ['name', 'domain', 'duration',
                    'category_id', 'category', 'consent_mode']

MALFORM_RESP = "malform_resp"

class ConsentResource:
    resource_type = 'consent_resource'
    lib_name = ''
    domains: List[str] = []
    pattern_name = ''
    url_path_pattern = ''

    def __init__(self, resource: Dict):
        self._resource = resource

    @classmethod
    def match_url(cls, cur_url, url_parts):
        if len(cls.domains) == 0:  # ignore domains, just use the url path, since the file may host on cdn
            return cls.match_url_path(url_parts.path)
        return (has_same_suffixed_domain(cur_url, url_parts.hostname) or cls.match_hostname(url_parts.hostname)) and cls.match_url_path(url_parts.path)

    @classmethod
    def match_hostname(cls, hostname: Optional[str]):
        if hostname is None:
            return False
        for domain in cls.domains:
            if hostname.endswith(domain):
                return True
        return False

    @classmethod
    def match_url_path(cls, url_path: Optional[str]):
        if url_path is None:
            return False
        return match_resource_paths(url_path, [cls.url_path_pattern])

    @classmethod
    def decode(cls, resource_content: str, warnings=None) -> Optional[pd.DataFrame]:
        raise NotImplementedError(f"{cls.pattern_name} not supported yet.")

    def normalize(self, raw_cookies: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def decode_and_normalize(self, resource_content: str, warnings=None) -> Optional[pd.DataFrame]:
        return self.normalize(self.decode(resource_content))

    @classmethod
    def get_cookie_list_from_file(cls, resource_file):
        resources = pd.read_json(resource_file)
        resource = find_one(resources, 'resource_type', 'consent_resource')
        if resource is None:
            raise ValueError("Resource file does not contain consent resource")
        # .decode_resource(resource.to_dict())
        return cls(resource).get_cookie_list()

    def get_cookie_list(self):
        response = self._resource['response']
        raw_cookie_list = self.decode(response)
        return self.normalize(raw_cookie_list)


if __name__ == '__main__':
    pass
    # %%
    import json
    from consent.util.default_path import get_data_dir
    resource_file = get_data_dir('2022-05-30/termly/termly.io/consent_resources.json')
    # SCAN_DIRS = list(SCAN_ROOT_DIR.glob('*'))
    # resource_file = get_data_dir('2021-08-13/pref_menu_scan_20k_30k/royalairmaroc.com') / 'consent_resources.json'
    resources = json.loads(resource_file.read_text())
    len(resources)
    # %%
    resources

# %%
    json.loads(resources[2]['response'])['DomainData']

# %%
    for r in resources:
        print(r['url'])
